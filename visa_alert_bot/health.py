from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def write_heartbeat(path: Path, now: datetime | None = None) -> None:
    """Record that the monitor event loop is alive without exposing private data."""
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = (now or datetime.now(UTC)).astimezone(UTC)
    path.write_text(timestamp.isoformat(), encoding="utf-8")


async def maintain_heartbeat(path: Path, interval_seconds: float = 60.0) -> None:
    """Refresh the monitor heartbeat until the task is cancelled."""
    while True:
        try:
            write_heartbeat(path)
        except OSError:
            LOGGER.exception("Could not update monitor heartbeat at %s", path)
        await asyncio.sleep(interval_seconds)
