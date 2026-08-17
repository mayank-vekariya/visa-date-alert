import unittest

from visa_alert_bot.detector import AlertLevel, MessageDetector


class MessageDetectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.detector = MessageDetector(
            (
                "B2",
                "B-2",
                "B1/B2",
                "B1 B2",
                "visitor visa",
                "tourist visa",
            ),
            (
                "Mumbai",
                "New Delhi",
                "Delhi",
                "MUM",
                "DEL",
            ),
            high_score=8,
            excluded_visas=("B1", "B-1", "H1B", "H-1B", "H1", "H4", "F1", "L1"),
            require_target_visa=True,
            require_target_location=True,
        )

    def test_strong_report_is_high(self) -> None:
        result = self.detector.detect("B1/B2 slots opened in Mumbai for September. Go check now!")
        self.assertEqual(result.level, AlertLevel.HIGH)
        self.assertGreaterEqual(result.score, 9)

    def test_slot_report_without_visa_or_location_is_low(self) -> None:
        result = self.detector.detect("Slots open")
        self.assertEqual(result.level, AlertLevel.LOW)

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

    def test_location_report_without_visa_is_low(self) -> None:
        result = self.detector.detect("Mumbai open")
        self.assertEqual(result.level, AlertLevel.LOW)

    def test_unrelated_open_message_is_low(self) -> None:
        result = self.detector.detect("The office is open for lunch")
        self.assertEqual(result.level, AlertLevel.LOW)

    def test_hinglish_report_is_detected(self) -> None:
        result = self.detector.detect("Mumbai B1/B2 slots aa gaye, hurry")
        self.assertEqual(result.level, AlertLevel.HIGH)

    def test_b2_bulk_report_is_detected(self) -> None:
        result = self.detector.detect("B2 bulk appointments New Delhi Dec 2026")
        self.assertEqual(result.level, AlertLevel.HIGH)

    def test_b2_targeted_report_is_high(self) -> None:
        result = self.detector.detect("B-2 slots available in New Delhi for December. Check now")
        self.assertEqual(result.level, AlertLevel.HIGH)

    def test_compact_b2_report_is_medium(self) -> None:
        result = self.detector.detect("B2 available in Mumbai for 07/27")
        self.assertEqual(result.level, AlertLevel.MEDIUM)

    def test_explicit_non_tourist_visa_is_rejected(self) -> None:
        result = self.detector.detect("H1B slots available in Hyderabad for December. Check now")
        self.assertEqual(result.level, AlertLevel.LOW)
        self.assertEqual(result.score, 0)

    def test_non_target_city_ofc_report_is_low(self) -> None:
        result = self.detector.detect("Chennai July OFC available")
        self.assertEqual(result.level, AlertLevel.LOW)

    def test_screenshot_new_delhi_format_is_high(self) -> None:
        result = self.detector.detect(
            "B1/B2 Slots Alert! Location: NEW DELHI OFC Available Dates: 1 "
            "Earliest Date: 21 Sep 26 Earliest Date Slots: 1"
        )
        self.assertEqual(result.level, AlertLevel.HIGH)

    def test_mumbai_without_month_is_high(self) -> None:
        result = self.detector.detect("B1/B2 Slots Alert! Location: MUMBAI OFC Available Dates: 1")
        self.assertEqual(result.level, AlertLevel.HIGH)

    def test_hyderabad_b1_b2_format_is_rejected(self) -> None:
        result = self.detector.detect(
            "B1/B2 Slots Alert! Location: HYDERABAD OFC Available Dates: 1 Earliest Date: 03 Nov 26"
        )
        self.assertEqual(result.level, AlertLevel.LOW)

    def test_na_abbreviation_is_rejected(self) -> None:
        result = self.detector.detect("NA 2 All")
        self.assertEqual(result.level, AlertLevel.LOW)
        self.assertEqual(result.score, 0)

    def test_unbookable_report_is_rejected(self) -> None:
        result = self.detector.detect("OFC available but no submit button")
        self.assertEqual(result.level, AlertLevel.LOW)

    def test_past_availability_is_not_an_alert(self) -> None:
        result = self.detector.detect("B2 slots were available yesterday")
        self.assertEqual(result.level, AlertLevel.LOW)

    def test_b2_question_without_question_mark_is_low(self) -> None:
        result = self.detector.detect("Any B2 dates for Dec")
        self.assertEqual(result.level, AlertLevel.LOW)

    def test_agent_advertisement_is_rejected(self) -> None:
        result = self.detector.detect("B2 slots available for December, low charges, ping me")
        self.assertEqual(result.level, AlertLevel.LOW)

    def test_short_alias_does_not_match_inside_another_word(self) -> None:
        result = self.detector.detect("B20 is available")
        self.assertEqual(result.level, AlertLevel.LOW)


if __name__ == "__main__":
    unittest.main()
