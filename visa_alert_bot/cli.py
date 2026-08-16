from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import urllib.request
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import AppConfig
from .detector import MessageDetector
from .telegram_monitor import list_chats, run_monitor


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="visa-alert",
        description="Watch selected Telegram groups for visa appointment reports.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "doctor",
        help="Check local configuration without printing secrets or sending alerts",
    )
    subparsers.add_parser(
        "find-alert-chat",
        help="Read Bot API updates and show chat IDs after you send the bot /start",
    )
    subparsers.add_parser("list-chats", help="Log in and list Telegram group/channel IDs")
    subparsers.add_parser("run", help="Start the Telegram monitor")
    check = subparsers.add_parser("check", help="Score sample text without using Telegram")
    check.add_argument("text", help="A sample Telegram message")
    return parser


def _configure_logging(root: Path) -> None:
    log_directory = root / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    file_handler = RotatingFileHandler(
        log_directory / "visa-alert.log",
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, handlers=[stream_handler, file_handler], force=True)
    logging.getLogger("telethon").setLevel(logging.WARNING)


def _check(config: AppConfig, text: str) -> int:
    detector = MessageDetector(
        config.target_visas,
        config.target_locations,
        config.medium_score,
        config.high_score,
        config.excluded_visas,
    )
    result = detector.detect(text)
    print(f"Level: {result.level.value.upper()}")
    print(f"Score: {result.score}")
    print("Reasons:")
    for reason in result.reasons:
        print(f"  - {reason}")
    return 0


def _doctor(config: AppConfig) -> int:
    required = (
        ("Telegram API credentials", bool(config.telegram_api_id and config.telegram_api_hash)),
        ("Telegram login phone", bool(config.telegram_phone)),
        ("At least one monitored chat", bool(config.monitored_chat_ids)),
    )
    optional = (
        ("Companion Telegram alert bot", config.alert_bot_ready),
        ("Local Telegram session", config.session_path.with_suffix(".session").exists()),
        ("Twilio account and phone numbers", config.twilio_ready),
        ("Twilio HIGH-alert calls enabled", config.enable_calls),
        ("Dry-run mode", config.dry_run),
    )

    print("Configuration doctor (secret values are never displayed)\n")
    for label, ready in required:
        print(f"[{'OK' if ready else '!!'}] {label}")
    for label, ready in optional:
        print(f"[{'OK' if ready else '--'}] {label}")

    if config.enable_calls and not config.twilio_ready:
        print("\n[!!] Calls are enabled, but the Twilio configuration is incomplete.")
        return 2
    if not all(ready for _, ready in required):
        print("\nFill the missing required values in .env, then run doctor again.")
        return 2
    print("\nRequired configuration is ready. No network calls or alerts were sent.")
    return 0


def _find_alert_chat(config: AppConfig) -> int:
    if not config.telegram_alert_bot_token:
        raise ValueError("TELEGRAM_ALERT_BOT_TOKEN is empty")
    endpoint = f"https://api.telegram.org/bot{config.telegram_alert_bot_token}/getUpdates"
    with urllib.request.urlopen(endpoint, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not payload.get("ok"):
        raise RuntimeError("Telegram Bot API rejected the getUpdates request")

    chats: dict[int, str] = {}
    for update in payload.get("result", []):
        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat") or {}
        if "id" not in chat:
            continue
        label = (
            chat.get("title")
            or chat.get("username")
            or " ".join(value for value in (chat.get("first_name"), chat.get("last_name")) if value)
            or chat.get("type", "chat")
        )
        chats[int(chat["id"])] = str(label)

    if not chats:
        print("No bot chats found. Open the bot in Telegram, send /start, and try again.")
        return 1
    print("Bot chats found (the bot token is not displayed):\n")
    for chat_id, label in sorted(chats.items(), key=lambda item: item[1].casefold()):
        print(f"{chat_id:>16}  {label}")
    print("\nCopy your private chat ID to TELEGRAM_ALERT_CHAT_ID in .env.")
    return 0


def main() -> None:
    args = _parser().parse_args()
    try:
        root = Path.cwd()
        _configure_logging(root)
        config = AppConfig.from_env(root)
        if args.command == "doctor":
            raise SystemExit(_doctor(config))
        if args.command == "find-alert-chat":
            raise SystemExit(_find_alert_chat(config))
        if args.command == "check":
            raise SystemExit(_check(config, args.text))
        if args.command == "list-chats":
            asyncio.run(list_chats(config))
        elif args.command == "run":
            asyncio.run(run_monitor(config))
    except (ValueError, RuntimeError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    except KeyboardInterrupt:
        print("\nVisa monitor stopped.")


if __name__ == "__main__":
    main()
