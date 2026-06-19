"""Service that notifies residents of alarms via the Meta WhatsApp Cloud API.

Elis Evleri flow: a field ESP32 POSTs to the FastAPI ``/alerts/sensor`` endpoint when
smoke/gas is detected; the endpoint calls this service, which sends a pre-approved
WhatsApp **template** message to every resident.

Follows CLAUDE.md rules: all I/O is async (``httpx.AsyncClient``), secrets are read
only from ``app.config``, and logs go through structlog with ``trace_id``.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import httpx

from app.config import settings
from app.logging import get_logger

log = get_logger(__name__)

# Turkish label for the sensor type, used in the template parameters.
_SENSOR_TR = {"smoke": "duman", "gas": "gaz"}


@dataclass
class SendResult:
    """Summary of a single alarm dispatch."""

    delivered: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


def parse_recipients(raw: str) -> list[str]:
    """Parse a comma-separated phone-number string into a cleaned list."""
    return [r.strip() for r in raw.split(",") if r.strip()]


class WhatsAppNotifier:
    """Sends template messages via the Meta WhatsApp Cloud API.

    Defaults are read from ``app.config.settings``; every field can also be passed
    explicitly so the notifier can be unit-tested in isolation.
    """

    def __init__(
        self,
        *,
        access_token: str | None = None,
        phone_number_id: str | None = None,
        api_version: str | None = None,
        template_name: str | None = None,
        template_lang: str | None = None,
        recipients: list[str] | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.access_token = (
            access_token if access_token is not None else settings.whatsapp_access_token
        )
        self.phone_number_id = (
            phone_number_id if phone_number_id is not None else settings.whatsapp_phone_number_id
        )
        self.api_version = api_version or settings.whatsapp_api_version
        self.template_name = template_name or settings.whatsapp_template_name
        self.template_lang = template_lang or settings.whatsapp_template_lang
        self.recipients = (
            recipients if recipients is not None else parse_recipients(settings.whatsapp_recipients)
        )
        self.timeout = timeout

    @property
    def endpoint(self) -> str:
        return f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"

    def is_configured(self) -> bool:
        return bool(self.access_token and self.phone_number_id and self.recipients)

    def _build_payload(self, to: str, params: list[str]) -> dict:
        return {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": self.template_name,
                "language": {"code": self.template_lang},
                "components": [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": p} for p in params],
                    }
                ],
            },
        }

    async def send_alert(
        self,
        *,
        building: str,
        floor: str,
        sensor: str,
        occurred_at: str,
    ) -> SendResult:
        """Send the alarm template to all recipients; tolerates partial failure.

        Template parameter order: ``{{1}}`` building, ``{{2}}`` floor, ``{{3}}`` sensor,
        ``{{4}}`` time.
        """
        result = SendResult()
        if not self.is_configured():
            log.warning("whatsapp_not_configured", recipients=len(self.recipients))
            return result

        sensor_tr = _SENSOR_TR.get(sensor, sensor)
        params = [building, str(floor), sensor_tr, occurred_at]
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:

            async def _send_one(to: str) -> tuple[str, str | None]:
                try:
                    resp = await client.post(
                        self.endpoint, headers=headers, json=self._build_payload(to, params)
                    )
                    resp.raise_for_status()
                    return to, None
                except httpx.HTTPError as exc:
                    return to, str(exc)

            outcomes = await asyncio.gather(*(_send_one(to) for to in self.recipients))

        for to, error in outcomes:
            if error is None:
                result.delivered += 1
                log.info("whatsapp_sent", to=to, sensor=sensor, floor=floor)
            else:
                result.failed += 1
                result.errors.append(f"{to}: {error}")
                log.error("whatsapp_failed", to=to, sensor=sensor, error=error)

        return result
