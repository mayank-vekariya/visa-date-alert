import unittest

from visa_alert_bot.detector import AlertLevel, MessageDetector


class MessageDetectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.detector = MessageDetector(
            (
                "B1/B2",
                "visitor visa",
                "tourist visa",
                "H1B",
                "H-1B",
                "H1",
                "H4",
                "Dropbox",
                "Interview Waiver",
                "IW",
            ),
            (
                "Mumbai",
                "Delhi",
                "Hyderabad",
                "Chennai",
                "Kolkata",
                "MUM",
                "DEL",
                "HYD",
                "CHN",
                "KOL",
            ),
        )

    def test_strong_report_is_high(self) -> None:
        result = self.detector.detect("B1/B2 slots opened in Mumbai for September. Go check now!")
        self.assertEqual(result.level, AlertLevel.HIGH)
        self.assertGreaterEqual(result.score, 9)

    def test_short_slot_report_is_medium(self) -> None:
        result = self.detector.detect("Slots open")
        self.assertEqual(result.level, AlertLevel.MEDIUM)

    def test_explicit_no_slots_is_rejected(self) -> None:
        result = self.detector.detect("No slots open in Mumbai today")
        self.assertEqual(result.level, AlertLevel.LOW)
        self.assertEqual(result.score, 0)

    def test_no_open_slots_word_order_is_rejected(self) -> None:
        result = self.detector.detect("No open slots in Mumbai today")
        self.assertEqual(result.level, AlertLevel.LOW)
        self.assertEqual(result.score, 0)

    def test_question_is_not_an_alert(self) -> None:
        result = self.detector.detect("When will B1/B2 slots open in Mumbai?")
        self.assertEqual(result.level, AlertLevel.LOW)

    def test_expired_report_is_not_an_alert(self) -> None:
        result = self.detector.detect("B1/B2 slots were open in Delhi but are already gone")
        self.assertEqual(result.level, AlertLevel.LOW)

    def test_opened_then_gone_is_rejected(self) -> None:
        result = self.detector.detect("B1/B2 slots opened in Delhi but are gone")
        self.assertEqual(result.level, AlertLevel.LOW)

    def test_compact_location_report_is_medium(self) -> None:
        result = self.detector.detect("Mumbai open")
        self.assertEqual(result.level, AlertLevel.MEDIUM)

    def test_unrelated_open_message_is_low(self) -> None:
        result = self.detector.detect("The office is open for lunch")
        self.assertEqual(result.level, AlertLevel.LOW)

    def test_hinglish_report_is_detected(self) -> None:
        result = self.detector.detect("Mumbai B1/B2 slots aa gaye, hurry")
        self.assertEqual(result.level, AlertLevel.HIGH)

    def test_h1b_bulk_report_is_detected(self) -> None:
        result = self.detector.detect("Bulk appointments Hyderabad Dec 2026")
        self.assertEqual(result.level, AlertLevel.MEDIUM)

    def test_h1b_targeted_report_is_high(self) -> None:
        result = self.detector.detect("H-1B slots available in Chennai for December. Check now")
        self.assertEqual(result.level, AlertLevel.HIGH)

    def test_compact_h4_report_is_medium(self) -> None:
        result = self.detector.detect("H4-1 available for 07/27")
        self.assertEqual(result.level, AlertLevel.MEDIUM)

    def test_city_ofc_report_is_medium(self) -> None:
        result = self.detector.detect("Chennai July OFC available")
        self.assertEqual(result.level, AlertLevel.MEDIUM)

    def test_na_abbreviation_is_rejected(self) -> None:
        result = self.detector.detect("NA 2 All")
        self.assertEqual(result.level, AlertLevel.LOW)
        self.assertEqual(result.score, 0)

    def test_unbookable_report_is_rejected(self) -> None:
        result = self.detector.detect("OFC available but no submit button")
        self.assertEqual(result.level, AlertLevel.LOW)

    def test_past_availability_is_not_an_alert(self) -> None:
        result = self.detector.detect("H1B slots were available yesterday")
        self.assertEqual(result.level, AlertLevel.LOW)

    def test_h1b_question_without_question_mark_is_low(self) -> None:
        result = self.detector.detect("Any H1B dates for Dec")
        self.assertEqual(result.level, AlertLevel.LOW)

    def test_agent_advertisement_is_rejected(self) -> None:
        result = self.detector.detect("H1B slots available for December, low charges, ping me")
        self.assertEqual(result.level, AlertLevel.LOW)

    def test_short_alias_does_not_match_inside_another_word(self) -> None:
        result = self.detector.detect("A preview is available")
        self.assertEqual(result.level, AlertLevel.LOW)


if __name__ == "__main__":
    unittest.main()
