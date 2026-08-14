import tempfile
import unittest
from pathlib import Path

from visa_alert_bot.singleton import SingleInstance


class SingleInstanceTests(unittest.TestCase):
    def test_second_monitor_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "monitor.lock"
            first = SingleInstance(path)
            second = SingleInstance(path)
            first.acquire()
            try:
                with self.assertRaisesRegex(RuntimeError, "already running"):
                    second.acquire()
            finally:
                first.release()


if __name__ == "__main__":
    unittest.main()
