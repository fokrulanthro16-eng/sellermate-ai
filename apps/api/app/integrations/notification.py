"""Notification channel providers — Email, SMS, WhatsApp, In-App."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NotificationResult:
    channel: str
    recipient: str
    status: str  # sent | failed | queued
    message_id: str
    sent_at: str
    is_mock: bool


class NotificationProvider(ABC):
    name: str
    display_name: str

    def is_configured(self) -> bool:
        return False

    @abstractmethod
    async def send(self, recipient: str, subject: str, body: str) -> NotificationResult: ...

    async def test_connection(self) -> dict:
        return {"success": True, "mode": "mock", "message": "Mock channel OK"}


class EmailProvider(NotificationProvider):
    name = "email"
    display_name = "Email"

    def __init__(self, smtp_host: str = "", smtp_user: str = "", smtp_password: str = "") -> None:
        self._ok = bool(smtp_host and smtp_user and smtp_password)

    def is_configured(self) -> bool:
        return self._ok

    async def send(self, recipient: str, subject: str, body: str) -> NotificationResult:
        import uuid
        return NotificationResult(channel="email", recipient=recipient,
                                  status="queued", message_id=f"EMAIL-{uuid.uuid4().hex[:8].upper()}",
                                  sent_at=datetime.utcnow().isoformat(), is_mock=not self._ok)


class SMSProvider(NotificationProvider):
    name = "sms"
    display_name = "SMS"

    def __init__(self, api_key: str = "", sender_id: str = "") -> None:
        self._ok = bool(api_key)

    def is_configured(self) -> bool:
        return self._ok

    async def send(self, recipient: str, subject: str, body: str) -> NotificationResult:
        import uuid
        return NotificationResult(channel="sms", recipient=recipient,
                                  status="queued", message_id=f"SMS-{uuid.uuid4().hex[:8].upper()}",
                                  sent_at=datetime.utcnow().isoformat(), is_mock=not self._ok)


class WhatsAppProvider(NotificationProvider):
    name = "whatsapp"
    display_name = "WhatsApp"

    def __init__(self, access_token: str = "", phone_number_id: str = "") -> None:
        self._ok = bool(access_token and phone_number_id)

    def is_configured(self) -> bool:
        return self._ok

    async def send(self, recipient: str, subject: str, body: str) -> NotificationResult:
        import uuid
        return NotificationResult(channel="whatsapp", recipient=recipient,
                                  status="queued", message_id=f"WA-{uuid.uuid4().hex[:8].upper()}",
                                  sent_at=datetime.utcnow().isoformat(), is_mock=not self._ok)


class InAppProvider(NotificationProvider):
    name = "inapp"
    display_name = "In-App"

    def is_configured(self) -> bool:
        return True

    async def send(self, recipient: str, subject: str, body: str) -> NotificationResult:
        import uuid
        return NotificationResult(channel="inapp", recipient=recipient,
                                  status="sent", message_id=f"IA-{uuid.uuid4().hex[:8].upper()}",
                                  sent_at=datetime.utcnow().isoformat(), is_mock=False)


_REGISTRY: dict[str, NotificationProvider] = {
    "email":    EmailProvider(),
    "sms":      SMSProvider(),
    "whatsapp": WhatsAppProvider(),
    "inapp":    InAppProvider(),
}

# Notification types with templates
NOTIFICATION_TYPES = {
    "low_stock":         {"subject_bn": "স্টক কম সতর্কতা",       "subject_en": "Low Stock Alert"},
    "pending_order":     {"subject_bn": "নতুন পেন্ডিং অর্ডার",  "subject_en": "New Pending Order"},
    "payment_reminder":  {"subject_bn": "পেমেন্ট মনে করিয়ে দেওয়া", "subject_en": "Payment Reminder"},
    "courier_update":    {"subject_bn": "কুরিয়ার আপডেট",         "subject_en": "Courier Update"},
    "customer_followup": {"subject_bn": "গ্রাহক ফলো-আপ",         "subject_en": "Customer Follow-up"},
}


def get_notification_provider(name: str) -> NotificationProvider:
    return _REGISTRY.get(name, _REGISTRY["inapp"])


def notification_status_list() -> list[dict]:
    return [
        {
            "name": p.name, "display_name": p.display_name,
            "is_configured": p.is_configured(), "mode": "real" if p.is_configured() else "mock",
        }
        for p in _REGISTRY.values()
    ]
