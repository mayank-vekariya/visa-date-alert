import tempfile
import unittest
from pathlib import Path

from visa_alert_bot.state import AlertState


class AlertStateTests(unittest.TestCase):
    def test_messages_are_processed_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = AlertState(Path(directory) / "state.sqlite3")
            self.assertTrue(state.mark_message_once(-100123, 7))
            self.assertFalse(state.mark_message_once(-100123, 7))
            state.close()

    def test_same_text_is_deduplicated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = AlertState(Path(directory) / "state.sqlite3")
            self.assertTrue(state.mark_alert_if_fresh("Slots OPEN!", 300))
            self.assertFalse(state.mark_alert_if_fresh("slots open", 300))
            state.close()


if __name__ == "__main__":
    unittest.main()
