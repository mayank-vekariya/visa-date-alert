from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum


class AlertLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class Detection:
    level: AlertLevel
    score: int
    reasons: tuple[str, ...]
    normalized_text: str


POSITIVE_PATTERNS: tuple[tuple[re.Pattern[str], int, str], ...] = (
    (re.compile(r"\bslots?\s+(?:(?:are|have)\s+)?open(?:ed)?\b"), 5, "slot-open phrase"),
    (
        re.compile(r"\b(?:slots?|appointments?)\s+(?:are\s+)?available\b"),
        5,
        "appointment available",
    ),
    (re.compile(r"\bdates?\s+(?:are\s+)?available\b"), 4, "date available"),
    (re.compile(r"\bbulk\s+(?:appointments?|dates?|slots?)\b"), 5, "bulk slot report"),
    (re.compile(r"\b(?:new|fresh)\s+dates?\b"), 4, "new dates"),
    (re.compile(r"\bbook\s+(?:it\s+)?now\b"), 3, "book now"),
    (re.compile(r"\bavailable\s+(?:right\s+)?now\b"), 4, "available now"),
    (re.compile(r"\b(?:still|currently)\s+available\b"), 4, "currently available"),
    (
        re.compile(r"\b(?:yes|go)\s+(?:\d+\s+)?(?:all|mum|del|hyd|chn|kol)\b"),
        5,
        "compact availability report",
    ),
    (re.compile(r"\bslots?\s+(?:aa|a)\s+gay[aei]\b"), 4, "slot reported in Hinglish"),
    (re.compile(r"\bslots?\s+khul(?:e|\s+gaye)?\b"), 4, "slot open in Hinglish"),
)

HARD_NEGATIVES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bn/?a\b"), "not-available abbreviation"),
    (
        re.compile(r"\bno\s+(?:(?:open|available)\s+)?(?:appointments?|dates?|slots?)\b"),
        "explicit no-slots statement",
    ),
    (
        re.compile(r"\b(?:slots?|appointments?|dates?)\s+(?:are\s+)?not\s+(?:open|available)\b"),
        "explicit not-open statement",
    ),
    (re.compile(r"\bnothing\s+(?:is\s+)?available\b"), "nothing available"),
    (re.compile(r"\b(?:slots?|appointments?)\s+(?:are\s+)?closed\b"), "slots closed"),
    (re.compile(r"\bfake\s+(?:news|alert|message)\b"), "fake report"),
    (
        re.compile(r"\b(?:all\s+)?(?:slots?|dates?)\s+(?:are\s+)?(?:gone|booked)\b"),
        "slots already gone",
    ),
    (
        re.compile(r"\b(?:but|now|already)\s+(?:(?:they\s+)?are\s+)?(?:closed|gone|booked)\b"),
        "reported opportunity has ended",
    ),
    (
        re.compile(
            r"\b(?:no\s+(?:submit\s+button|consular)|not\s+able\s+to\s+(?:book|schedule|submit))\b"
        ),
        "reported appointment cannot be submitted",
    ),
    (
        re.compile(r"\b(?:(?:dm|inbox|ping|contact)\s+me|agents?|low\s+charges|pay\s+after)\b"),
        "promotional or agent message",
    ),
)

QUESTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bwhen\s+(?:will|do|are)\b"),
    re.compile(r"\b(?:anyone|somebody)\s+(?:see|saw|know|check)\b"),
    re.compile(r"\b(?:are|is|any)\s+(?:there\s+)?(?:appointments?|dates?|slots?)\b"),
    re.compile(r"\bcan\s+(?:anyone|someone|somebody)\b"),
    re.compile(r"\bany\b.*\b(?:appointments?|dates?|slots?)\b"),
)

EXPIRED_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:was|were)\s+open\b"),
    re.compile(r"\b(?:was|were)\s+available\b"),
    re.compile(r"\bopened\s+(?:earlier|yesterday|last\s+night)\b"),
    re.compile(r"\b(?:already|just)\s+(?:closed|gone)\b"),
)

URGENCY_WORDS = ("hurry", "urgent", "asap", "go check", "check now", "right now")
MONTHS = (
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
    "jan",
    "feb",
    "mar",
    "apr",
    "jun",
    "jul",
    "aug",
    "sep",
    "sept",
    "oct",
    "nov",
    "dec",
)


def normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = re.sub(r"[^\w\s/?:+-]", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _term_pattern(value: str) -> re.Pattern[str]:
    """Match configured aliases as terms, not substrings such as IW in preview."""
    escaped = re.escape(normalize(value)).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<!\w){escaped}(?!\w)")


class MessageDetector:
    def __init__(
        self,
        target_visas: tuple[str, ...],
        target_locations: tuple[str, ...],
        medium_score: int = 5,
        high_score: int = 8,
        excluded_visas: tuple[str, ...] = (),
        require_target_visa: bool = False,
        require_target_location: bool = False,
    ) -> None:
        self.target_visas = tuple(normalize(value) for value in target_visas)
        self.excluded_visas = tuple(normalize(value) for value in excluded_visas)
        self.target_locations = tuple(normalize(value) for value in target_locations)
        self._visa_patterns = tuple(_term_pattern(value) for value in self.target_visas)
        self._excluded_visa_patterns = tuple(_term_pattern(value) for value in self.excluded_visas)
        self._location_patterns = tuple(_term_pattern(value) for value in self.target_locations)
        self.medium_score = medium_score
        self.high_score = high_score
        self.require_target_visa = require_target_visa
        self.require_target_location = require_target_location

    def detect(self, text: str) -> Detection:
        value = normalize(text)
        if not value:
            return Detection(AlertLevel.LOW, 0, ("empty message",), value)

        for pattern, reason in HARD_NEGATIVES:
            if pattern.search(value):
                return Detection(AlertLevel.LOW, 0, (reason,), value)

        score = 0
        reasons: list[str] = []
        positive_scores: list[tuple[int, str]] = []
        for pattern, weight, reason in POSITIVE_PATTERNS:
            if pattern.search(value):
                positive_scores.append((weight, reason))

        # Similar positive phrases should not inflate one report; use the strongest one.
        if positive_scores:
            weight, reason = max(positive_scores)
            score += weight
            reasons.append(f"+{weight} {reason}")

        visas = [
            visa
            for visa, pattern in zip(self.target_visas, self._visa_patterns, strict=True)
            if visa and pattern.search(value)
        ]
        excluded_visas = [
            visa
            for visa, pattern in zip(self.excluded_visas, self._excluded_visa_patterns, strict=True)
            if visa and pattern.search(value)
        ]
        if excluded_visas and not visas:
            return Detection(
                AlertLevel.LOW,
                0,
                (f"non-target visa category ({excluded_visas[0]})",),
                value,
            )
        if self.require_target_visa and not visas:
            return Detection(AlertLevel.LOW, 0, ("target visa category required",), value)
        if visas:
            score += 2
            reasons.append(f"+2 target visa ({visas[0]})")

        locations = [
            location
            for location, pattern in zip(
                self.target_locations, self._location_patterns, strict=True
            )
            if location and pattern.search(value)
        ]
        if self.require_target_location and not locations:
            return Detection(AlertLevel.LOW, 0, ("target location required",), value)
        if locations:
            score += 1
            reasons.append(f"+1 target location ({locations[0]})")

        # Covers compact reports such as "Mumbai open" without treating every use of
        # the word "open" as an appointment report.
        if locations and not positive_scores and re.search(r"\bopen(?:ed)?\b", value):
            score += 4
            reasons.append("+4 target location reported open")

        if not positive_scores and re.search(r"\bavailable\b", value):
            if re.search(r"\b(?:appointments?|consular|ofc|slots?|vac)\b", value):
                score += 5
                reasons.append("+5 appointment context reported available")
            elif (
                visas
                or locations
                or any(re.search(rf"\b{re.escape(month)}\b", value) for month in MONTHS)
            ):
                score += 4
                reasons.append("+4 targeted availability report")

        urgency = next((word for word in URGENCY_WORDS if word in value), None)
        if urgency:
            score += 2
            reasons.append(f"+2 urgency ({urgency})")

        if any(re.search(rf"\b{re.escape(month)}\b", value) for month in MONTHS):
            score += 1
            reasons.append("+1 appointment month")

        if any(pattern.search(value) for pattern in EXPIRED_PATTERNS):
            score -= 6
            reasons.append("-6 past or expired report")

        if "?" in value:
            score -= 2
            reasons.append("-2 question mark")

        if any(pattern.search(value) for pattern in QUESTION_PATTERNS):
            score -= 4
            reasons.append("-4 information-seeking question")

        score = max(score, 0)
        if score >= self.high_score:
            level = AlertLevel.HIGH
        elif score >= self.medium_score:
            level = AlertLevel.MEDIUM
        else:
            level = AlertLevel.LOW
        return Detection(level, score, tuple(reasons) or ("no slot signal",), value)
