from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from .alerts import Alert, AlertDispatcher
from .config import AppConfig
from .detector import AlertLevel, MessageDetector
from .singleton import SingleInstance
from .state import AlertState

LOGGER = logging.getLogger(__name__)


def _telegram_client(config: AppConfig) -> Any:
    from telethon import TelegramClient

    config.session_path.parent.mkdir(parents=True, exist_ok=True)
    return TelegramClient(
        str(config.session_path),
        config.telegram_api_id,
        config.telegram_api_hash,
        auto_reconnect=True,
        connection_retries=10,
        retry_delay=2,
    )


async def _start_client(client: Any, config: AppConfig) -> None:
    phone = config.telegram_phone or None
    await client.start(phone=phone)


async def list_chats(config: AppConfig) -> None:
    config.require_telegram_credentials()
    client = _telegram_client(config)
    await _start_client(client, config)
    try:
        print("\nTelegram groups and channels:\n")
        rows: list[tuple[int, str, str]] = []
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                username = getattr(dialog.entity, "username", None) or ""
                rows.append((int(dialog.id), str(dialog.name), str(username)))
        for chat_id, title, username in sorted(rows, key=lambda row: row[1].casefold()):
            suffix = f" (@{username})" if username else ""
            print(f"{chat_id:>16}  {title}{suffix}")
        print("\nCopy only the desired IDs into MONITORED_CHAT_IDS in .env.")
    finally:
        await client.disconnect()


def _message_link(chat: Any, chat_id: int, message_id: int) -> str:
    username = getattr(chat, "username", None)
    if username:
        return f"https://t.me/{username}/{message_id}"
    raw_id = str(abs(chat_id))
    if raw_id.startswith("100"):
        raw_id = raw_id[3:]
        return f"https://t.me/c/{raw_id}/{message_id}"
    return ""


def _is_monitored_chat(chat_id: int | None, monitored_chat_ids: frozenset[int]) -> bool:
    """Filter by numeric ID without resolving pending/private chats at startup."""
    return chat_id is not None and int(chat_id) in monitored_chat_ids


async def run_monitor(config: AppConfig) -> None:
    config.require_telegram_credentials()
    config.require_monitored_chats()
    if (config.enable_calls or config.enable_sms) and not config.twilio_ready:
        raise ValueError("Calls/SMS are enabled, but one or more Twilio settings are empty")

    lock = SingleInstance(config.database_path.parent / "monitor.lock")
    with lock:
        await _run_monitor_locked(config)


async def _run_monitor_locked(config: AppConfig) -> None:
    from telethon import events

    client = _telegram_client(config)
    await _start_client(client, config)
    detector = MessageDetector(
        config.target_visas,
        config.target_locations,
        config.medium_score,
        config.high_score,
    )
    state = AlertState(config.database_path)
    state.prune()
    dispatcher = AlertDispatcher(config, client)
    monitored_chat_ids = frozenset(config.monitored_chat_ids)

    @client.on(events.NewMessage(incoming=True))
    async def on_message(event: Any) -> None:
        if not _is_monitored_chat(event.chat_id, monitored_chat_ids):
            return
        text = (event.raw_text or "").strip()
        if not text or not state.mark_message_once(int(event.chat_id), int(event.id)):
            return

        detection = detector.detect(text)
        LOGGER.info(
            "Scored message chat=%s id=%s level=%s score=%s reasons=%s",
            event.chat_id,
            event.id,
            detection.level.value,
            detection.score,
            "; ".join(detection.reasons),
        )
        if detection.level == AlertLevel.LOW:
            return
        if not state.mark_alert_if_fresh(text, config.dedup_window_seconds):
            LOGGER.info("Skipped a duplicate alert within the deduplication window")
            return

        chat = await event.get_chat()
        sender = await event.get_sender()
        chat_title = (
            getattr(chat, "title", None) or getattr(chat, "username", None) or str(event.chat_id)
        )
        sender_name = (
            getattr(sender, "first_name", None)
            or getattr(sender, "title", None)
            or getattr(sender, "username", None)
            or str(event.sender_id or "unknown")
        )
        alert = Alert(
            detection=detection,
            text=text,
            chat_title=str(chat_title),
            sender_name=str(sender_name),
            message_link=_message_link(chat, int(event.chat_id), int(event.id)),
            received_at=datetime.now(UTC),
        )
        await dispatcher.dispatch(alert)

    me = await client.get_me()
    LOGGER.warning(
        "Visa monitor is live as @%s. Watching %d chat(s). Dry run: %s",
        getattr(me, "username", None) or getattr(me, "first_name", "Telegram user"),
        len(monitored_chat_ids),
        config.dry_run,
    )
    try:
        await client.run_until_disconnected()
    finally:
        state.close()
