from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_env_file(path: Path) -> None:
    """Load a small .env file without overwriting real environment variables."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def _csv(name: str, default: str = "") -> tuple[str, ...]:
    return tuple(item.strip() for item in os.getenv(name, default).split(",") if item.strip())


def _ints(name: str, default: str = "") -> tuple[int, ...]:
    values = _csv(name, default)
    try:
        return tuple(int(value) for value in values)
    except ValueError as exc:
        raise ValueError(f"{name} must be a comma-separated list of whole numbers") from exc


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AppConfig:
    telegram_api_id: int | None
    telegram_api_hash: str
    telegram_phone: str
    telegram_alert_bot_token: str
    telegram_alert_chat_id: int | None
    monitored_chat_ids: tuple[int, ...]
    target_visas: tuple[str, ...]
    excluded_visas: tuple[str, ...]
    target_locations: tuple[str, ...]
    require_target_visa: bool
    require_target_location: bool
    medium_score: int
    high_score: int
    alert_repeat_delays: tuple[int, ...]
    dedup_window_seconds: int
    dry_run: bool
    session_path: Path
    database_path: Path
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_from_number: str
    alert_to_number: str
    twilio_twiml_url: str
    enable_calls: bool
    enable_sms: bool

    @classmethod
    def from_env(cls, root: Path | None = None) -> AppConfig:
        root = (root or Path.cwd()).resolve()
        load_env_file(root / ".env")

        raw_api_id = os.getenv("TELEGRAM_API_ID", "").strip()
        try:
            api_id = int(raw_api_id) if raw_api_id else None
        except ValueError as exc:
            raise ValueError("TELEGRAM_API_ID must be a whole number") from exc

        raw_alert_chat_id = os.getenv("TELEGRAM_ALERT_CHAT_ID", "").strip()
        try:
            alert_chat_id = int(raw_alert_chat_id) if raw_alert_chat_id else None
        except ValueError as exc:
            raise ValueError("TELEGRAM_ALERT_CHAT_ID must be a whole number") from exc

        data_dir = root / "data"
        medium_score = int(os.getenv("MEDIUM_SCORE", "5"))
        high_score = int(os.getenv("HIGH_SCORE", "8"))
        if high_score <= medium_score:
            raise ValueError("HIGH_SCORE must be greater than MEDIUM_SCORE")

        return cls(
            telegram_api_id=api_id,
            telegram_api_hash=os.getenv("TELEGRAM_API_HASH", "").strip(),
            telegram_phone=os.getenv("TELEGRAM_PHONE", "").strip(),
            telegram_alert_bot_token=os.getenv("TELEGRAM_ALERT_BOT_TOKEN", "").strip(),
            telegram_alert_chat_id=alert_chat_id,
            monitored_chat_ids=_ints("MONITORED_CHAT_IDS"),
            target_visas=_csv(
                "TARGET_VISAS",
                "B2,B-2,B1/B2,B1 B2,tourist visa,visitor visa",
            ),
            excluded_visas=_csv(
                "EXCLUDED_VISAS",
                "B1,B-1,H1B,H-1B,H1,H-1,H4,H-4,F1,F-1,L1,L-1,O1,O-1,J1,J-1",
            ),
            target_locations=_csv(
                "TARGET_LOCATIONS",
                "Mumbai,New Delhi,Delhi,MUM,DEL",
            ),
            require_target_visa=_bool("REQUIRE_TARGET_VISA", True),
            require_target_location=_bool("REQUIRE_TARGET_LOCATION", True),
            medium_score=medium_score,
            high_score=high_score,
            alert_repeat_delays=_ints("ALERT_REPEAT_DELAYS", "20,60"),
            dedup_window_seconds=int(os.getenv("DEDUP_WINDOW_SECONDS", "300")),
            dry_run=_bool("DRY_RUN"),
            session_path=data_dir / "telegram_visa_monitor",
            database_path=data_dir / "alerts.sqlite3",
            twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID", "").strip(),
            twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN", "").strip(),
            twilio_from_number=os.getenv("TWILIO_FROM_NUMBER", "").strip(),
            alert_to_number=os.getenv("ALERT_TO_NUMBER", "").strip(),
            twilio_twiml_url=os.getenv("TWILIO_TWIML_URL", "").strip(),
            enable_calls=_bool("ENABLE_CALLS"),
            enable_sms=_bool("ENABLE_SMS"),
        )

    def require_telegram_credentials(self) -> None:
        if not self.telegram_api_id or not self.telegram_api_hash:
            raise ValueError(
                "TELEGRAM_API_ID and TELEGRAM_API_HASH are required. "
                "Copy .env.example to .env and fill them in first."
            )

    def require_monitored_chats(self) -> None:
        if not self.monitored_chat_ids:
            raise ValueError(
                "MONITORED_CHAT_IDS is empty. Run `visa-alert list-chats`, then add "
                "the visa group/channel IDs to .env."
            )

    @property
    def twilio_ready(self) -> bool:
        return all(
            (
                self.twilio_account_sid,
                self.twilio_auth_token,
                self.twilio_from_number,
                self.alert_to_number,
            )
        )

    @property
    def alert_bot_ready(self) -> bool:
        return bool(self.telegram_alert_bot_token and self.telegram_alert_chat_id)

    @property
    def heartbeat_path(self) -> Path:
        return self.database_path.parent / "monitor.heartbeat"
