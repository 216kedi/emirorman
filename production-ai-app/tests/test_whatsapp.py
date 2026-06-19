import json

import httpx
import respx

from services.notifications import WhatsAppNotifier
from services.notifications.whatsapp import parse_recipients


def _notifier(recipients: list[str]) -> WhatsAppNotifier:
    return WhatsAppNotifier(
        access_token="TESTTOKEN",
        phone_number_id="123456",
        api_version="v21.0",
        template_name="elis_alarm",
        template_lang="tr",
        recipients=recipients,
    )


def test_parse_recipients_trims_and_drops_empties():
    assert parse_recipients(" +9011, ,+9022 ") == ["+9011", "+9022"]
    assert parse_recipients("") == []


async def test_send_alert_fans_out_to_all_recipients():
    notifier = _notifier(["+905551112233", "+905554445566"])
    with respx.mock(base_url="https://graph.facebook.com") as mock:
        route = mock.post("/v21.0/123456/messages").mock(
            return_value=httpx.Response(200, json={"messages": [{"id": "wamid.x"}]})
        )
        result = await notifier.send_alert(
            building="Elis Evleri", floor="0", sensor="gas", occurred_at="2026-06-19 10:00"
        )
    assert result.delivered == 2
    assert result.failed == 0
    assert route.call_count == 2


async def test_send_alert_payload_shape_and_tr_translation():
    notifier = _notifier(["+905551112233"])
    with respx.mock(base_url="https://graph.facebook.com") as mock:
        route = mock.post("/v21.0/123456/messages").mock(return_value=httpx.Response(200, json={}))
        await notifier.send_alert(
            building="Elis Evleri", floor="2", sensor="smoke", occurred_at="2026-06-19 10:00"
        )

    request = route.calls.last.request
    payload = json.loads(request.content)
    assert payload["messaging_product"] == "whatsapp"
    assert payload["to"] == "+905551112233"
    assert payload["type"] == "template"
    assert payload["template"]["name"] == "elis_alarm"
    assert payload["template"]["language"]["code"] == "tr"
    params = [p["text"] for p in payload["template"]["components"][0]["parameters"]]
    assert params == ["Elis Evleri", "2", "duman", "2026-06-19 10:00"]  # smoke -> duman
    assert request.headers["Authorization"] == "Bearer TESTTOKEN"


async def test_send_alert_tolerates_partial_failure():
    notifier = _notifier(["+901", "+902"])

    def _switch(request: httpx.Request) -> httpx.Response:
        to = json.loads(request.content)["to"]
        if to == "+902":
            return httpx.Response(400, json={"error": {"message": "bad number"}})
        return httpx.Response(200, json={})

    with respx.mock(base_url="https://graph.facebook.com") as mock:
        mock.post("/v21.0/123456/messages").mock(side_effect=_switch)
        result = await notifier.send_alert(building="B", floor="0", sensor="gas", occurred_at="t")
    assert result.delivered == 1
    assert result.failed == 1
    assert len(result.errors) == 1


async def test_not_configured_is_noop():
    notifier = WhatsAppNotifier(access_token="", phone_number_id="", recipients=[])
    assert notifier.is_configured() is False
    result = await notifier.send_alert(building="B", floor="0", sensor="gas", occurred_at="t")
    assert result.delivered == 0
    assert result.failed == 0
