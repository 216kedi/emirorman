import httpx
import respx
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

import app.routes.alerts as alerts_module
from app.config import settings
from services.notifications import WhatsAppNotifier

META_PATH = "/v21.0/123456/messages"


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(alerts_module.router)
    return app


def _configure(monkeypatch) -> None:
    monkeypatch.setattr(settings, "api_key", "secret")
    monkeypatch.setattr(settings, "alert_cooldown_seconds", 60)
    monkeypatch.setattr(settings, "building_name", "Elis Evleri")
    alerts_module._last_sent.clear()
    alerts_module._notifier = WhatsAppNotifier(
        access_token="TESTTOKEN",
        phone_number_id="123456",
        api_version="v21.0",
        recipients=["+905551112233"],
    )


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_requires_api_key(monkeypatch):
    _configure(monkeypatch)
    async with _client(_build_app()) as client:
        resp = await client.post(
            "/alerts/sensor", json={"device_id": "g1", "floor": "0", "sensor": "gas"}
        )
    assert resp.status_code == 401


async def test_alarm_sends_whatsapp(monkeypatch):
    _configure(monkeypatch)
    with respx.mock(base_url="https://graph.facebook.com") as mock:
        mock.post(META_PATH).mock(return_value=httpx.Response(200, json={}))
        async with _client(_build_app()) as client:
            resp = await client.post(
                "/alerts/sensor",
                headers={"x-api-key": "secret"},
                json={"device_id": "g1", "floor": "0", "sensor": "gas"},
            )
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "accepted"
    assert body["delivered"] == 1
    assert body["failed"] == 0


async def test_cooldown_suppresses_duplicate(monkeypatch):
    _configure(monkeypatch)
    with respx.mock(base_url="https://graph.facebook.com") as mock:
        mock.post(META_PATH).mock(return_value=httpx.Response(200, json={}))
        async with _client(_build_app()) as client:
            payload = {"device_id": "g1", "floor": "0", "sensor": "gas"}
            first = await client.post(
                "/alerts/sensor", headers={"x-api-key": "secret"}, json=payload
            )
            second = await client.post(
                "/alerts/sensor", headers={"x-api-key": "secret"}, json=payload
            )
    assert first.json()["status"] == "accepted"
    assert second.json()["status"] == "suppressed"


async def test_clear_state_is_ignored(monkeypatch):
    _configure(monkeypatch)
    async with _client(_build_app()) as client:
        resp = await client.post(
            "/alerts/sensor",
            headers={"x-api-key": "secret"},
            json={"device_id": "g1", "floor": "0", "sensor": "smoke", "state": "clear"},
        )
    assert resp.status_code == 202
    assert resp.json()["status"] == "ignored"
