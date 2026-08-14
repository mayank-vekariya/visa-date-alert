from __future__ import annotations

import asyncio
import html
import json
import logging
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .config import AppConfig
from .detector import AlertLevel, Detection

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Alert:
    detection: Detection
    text: str
    chat_title: str
    sender_name: str
    message_link: str
    received_at: datetime

    def telegram_text(self, reminder: bool = False) -> str:
        heading = "REMINDER - " if reminder else ""
        heading += (
            f"VISA SLOT ALERT ({self.detection.level.value.upper()}, score {self.detection.score})"
        )
        details = [
            heading,
            f"Group: {self.chat_title}",
            f"Sender: {self.sender_name}",
            f"Time: {self.received_at.astimezone().strftime('%Y-%m-%d %I:%M:%S %p %Z')}",
            "",
            self.text,
        ]
        if self.message_link:
            details.extend(("", f"Open original: {self.message_link}"))
        return "\n".join(details)

    def voice_text(self) -> str:
        return (
            f"Urgent visa alert. A {self.detection.level.value} confidence appointment "
            f"report was posted in {self.chat_title}. Check Telegram immediately."
        )


class AlertDispatcher:
    def __init__(self, config: AppConfig, telegram_client: Any) -> None:
        self.config = config
        self.telegram_client = telegram_client
        self._tasks: set[asyncio.Task[None]] = set()

    async def dispatch(self, alert: Alert) -> None:
        if self.config.dry_run:
            LOGGER.warning("DRY RUN\n%s", alert.telegram_text())
            return

        await self._send_initial_notifications(alert.telegram_text())

        if self.config.enable_sms:
            await self._send_twilio_sms(alert)
        if alert.detection.level == AlertLevel.HIGH and self.config.enable_calls:
            await self._make_twilio_call(alert)

        for delay in self.config.alert_repeat_delays:
            task = asyncio.create_task(self._send_reminder_after(delay, alert))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

    async def _send_saved_message(self, text: str) -> None:
        await self.telegram_client.send_message("me", text, link_preview=False)

    async def _send_initial_notifications(self, text: str) -> None:
        tasks = [self._send_saved_message(text)]
        if self.config.alert_bot_ready:
            tasks.append(self._send_alert_bot_message(text))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                LOGGER.error("An initial alert channel failed: %s", result)

    async def _send_alert_bot_message(self, text: str) -> None:
        def send() -> None:
            endpoint = (
                f"https://api.telegram.org/bot{self.config.telegram_alert_bot_token}/sendMessage"
            )
            body = urllib.parse.urlencode(
                {
                    "chat_id": str(self.config.telegram_alert_chat_id),
                    "text": text,
                    "disable_web_page_preview": "true",
                }
            ).encode("utf-8")
            request = urllib.request.Request(endpoint, data=body, method="POST")
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if not payload.get("ok"):
                raise RuntimeError("Telegram alert bot rejected the message")

        await asyncio.to_thread(send)

    async def _send_reminder_after(self, delay: int, alert: Alert) -> None:
        await asyncio.sleep(delay)
        try:
            text = alert.telegram_text(reminder=True)
            if self.config.alert_bot_ready:
                await self._send_alert_bot_message(text)
            else:
                await self._send_saved_message(text)
        except Exception:
            LOGGER.exception("Could not send the alert reminder")

    def _twilio_client(self) -> Any:
        if not self.config.twilio_ready:
            raise RuntimeError(
                "Twilio alerting is enabled but its account SID, auth token, from number, "
                "or destination number is missing"
            )
        from twilio.rest import Client

        return Client(self.config.twilio_account_sid, self.config.twilio_auth_token)

    async def _make_twilio_call(self, alert: Alert) -> None:
        def create_call() -> str:
            client = self._twilio_client()
            call_options: dict[str, str] = {
                "to": self.config.alert_to_number,
                "from_": self.config.twilio_from_number,
            }
            if self.config.twilio_twiml_url:
                call_options["url"] = self.config.twilio_twiml_url
            else:
                call_options["twiml"] = (
                    f"<Response><Say>{html.escape(alert.voice_text())}</Say></Response>"
                )
            call = client.calls.create(
                **call_options,
            )
            return str(call.sid)

        try:
            sid = await asyncio.to_thread(create_call)
            LOGGER.info("Started Twilio call %s", sid)
        except Exception:
            LOGGER.exception("Could not start the Twilio phone call")

    async def _send_twilio_sms(self, alert: Alert) -> None:
        def create_sms() -> str:
            client = self._twilio_client()
            message = client.messages.create(
                to=self.config.alert_to_number,
                from_=self.config.twilio_from_number,
                body=alert.telegram_text()[:1500],
            )
            return str(message.sid)

        try:
            sid = await asyncio.to_thread(create_sms)
            LOGGER.info("Sent Twilio SMS %s", sid)
        except Exception:
            LOGGER.exception("Could not send the Twilio SMS")
