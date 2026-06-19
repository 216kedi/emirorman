"""Elis Evleri sensor alarm endpoint.

Field ESP32 devices POST here when smoke/gas is detected; the server notifies all
residents via the Meta WhatsApp Cloud API. Requests are authenticated with the
existing ``x-api-key`` mechanism (``app.auth.require_api_key``).

A simple per-``(floor, sensor)`` cooldown prevents alarm storms (bouncing inputs or
repeated triggers).
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import require_api_key
from app.config import settings
from app.logging import get_logger
from services.notifications import WhatsAppNotifier

log = get_logger(__name__)
router = APIRouter(tags=["alerts"])

_notifier = WhatsAppNotifier()

# (floor, sensor) -> last send time (monotonic seconds).
_last_sent: dict[tuple[str, str], float] = {}


class SensorAlertRequest(BaseModel):
    device_id: str
    floor: str
    sensor: Literal["smoke", "gas"]
    state: Literal["alarm", "clear"] = "alarm"
    occurred_at: str | None = None


class AlertResponse(BaseModel):
    status: str
    delivered: int = 0
    failed: int = 0


@router.post("/alerts/sensor", status_code=202)
async def sensor_alert(
    body: SensorAlertRequest,
    _key: str = Depends(require_api_key),
) -> AlertResponse:
    log.info(
        "alert_received",
        device_id=body.device_id,
        floor=body.floor,
        sensor=body.sensor,
        state=body.state,
    )

    if body.state != "alarm":
        return AlertResponse(status="ignored")

    key = (body.floor, body.sensor)
    now = time.monotonic()
    last = _last_sent.get(key)
    if last is not None and (now - last) < settings.alert_cooldown_seconds:
        log.info("alert_suppressed_cooldown", floor=body.floor, sensor=body.sensor)
        return AlertResponse(status="suppressed")
    _last_sent[key] = now

    occurred_at = body.occurred_at or datetime.now(UTC).strftime("%Y-%m-%d %H:%M")
    result = await _notifier.send_alert(
        building=settings.building_name,
        floor=body.floor,
        sensor=body.sensor,
        occurred_at=occurred_at,
    )
    return AlertResponse(status="accepted", delivered=result.delivered, failed=result.failed)
