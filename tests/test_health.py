import asyncio
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from visa_alert_bot.health import maintain_heartbeat, write_heartbeat


class HeartbeatTests(unittest.IsolatedAsyncioTestCase):
    def test_write_heartbeat_records_utc_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data" / "monitor.heartbeat"
            expected = datetime(2026, 8, 15, 12, 30, tzinfo=UTC)

            write_heartbeat(path, expected)

            self.assertEqual(path.read_text(encoding="utf-8"), expected.isoformat())

    async def test_maintain_heartbeat_refreshes_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "monitor.heartbeat"
            task = asyncio.create_task(maintain_heartbeat(path, interval_seconds=0.01))
            try:
                await asyncio.sleep(0.03)
                first_timestamp = datetime.fromisoformat(path.read_text(encoding="utf-8"))
                await asyncio.sleep(0.03)
                second_timestamp = datetime.fromisoformat(path.read_text(encoding="utf-8"))
            finally:
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task

            self.assertGreater(second_timestamp, first_timestamp)


if __name__ == "__main__":
    unittest.main()
