# Selecting Telegram sources

Telegram appointment groups are unofficial, change frequently, and can attract
scammers. The safest setup combines one high-signal moderated group with one
larger public fallback, then lets the detector suppress questions and promotions.

## Tourist-visa sources evaluated on 2026-08-15

These public handles are examples, not endorsements or guarantees:

| Source | Focus | Practical note |
| --- | --- | --- |
| [@USvisaAppointmentsHelp](https://t.me/USvisaAppointmentsHelp) | U.S. B1/B2 slots and help in India | Public B1/B2-focused source; still verify every report |
| [@VisaAppointmentsIndia](https://t.me/VisaAppointmentsIndia) | Multiple U.S. visa categories in India | Broad public fallback; verify the visa category carefully |

For a B-2-only installation, prefer focused B1/B2 sources. A broad source may use
short messages that do not name a visa category, so it can create ambiguous alerts.

Do not copy IDs from another installation. Join a source yourself, review its
recent messages, run `visa-alert list-chats`, and add the ID shown by your own
Telegram session. A pending join request cannot be monitored until approved.

## Quality checklist

Prefer sources that:

- post current slot availability rather than predictions;
- clearly label B-2 or combined B-1/B-2 tourist slots, OFC/VAC, and consular slots;
- use clear city and month context;
- prohibit agents, paid booking offers, and direct-message solicitation;
- remain active without flooding members with unrelated discussion.

Avoid alerts that ask for payment, credentials, DS-160 access, one-time codes, or
remote-control access. Never give a group member a visa-site password or Telegram
login code. Confirm every report on the official appointment site yourself.

## Detector tuning

Test representative phrases before changing thresholds:

```powershell
visa-alert check "B2 bulk appointments New Delhi Dec 2026"
visa-alert check "OFC available but no submit button"
visa-alert check "Any B2 dates for Dec"
visa-alert check "B2 slots available, low charges, ping me"
visa-alert check "B1/B2 slots available in Hyderabad. Check now"
```

The first is a possible alert. The other four should remain LOW because they are
unbookable, questions, promotional, or explicitly outside the tourist category.
