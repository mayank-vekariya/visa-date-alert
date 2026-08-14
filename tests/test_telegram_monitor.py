import unittest

from visa_alert_bot.telegram_monitor import _is_monitored_chat


class TelegramMonitorFilterTests(unittest.TestCase):
    def test_selected_chat_is_accepted(self) -> None:
        self.assertTrue(_is_monitored_chat(-100123, frozenset((-100123, -100456))))

    def test_unselected_or_missing_chat_is_rejected(self) -> None:
        monitored = frozenset((-100123,))
        self.assertFalse(_is_monitored_chat(-100999, monitored))
        self.assertFalse(_is_monitored_chat(None, monitored))


if __name__ == "__main__":
    unittest.main()
