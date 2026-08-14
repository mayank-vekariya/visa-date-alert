# Selecting Telegram sources

Telegram appointment groups are unofficial, change frequently, and can attract
scammers. The safest setup combines one high-signal moderated group with one
larger public fallback, then lets the detector suppress questions and promotions.

## Sources evaluated on 2026-08-14

These public handles are examples, not endorsements or guarantees:

| Source | Focus | Practical note |
| --- | --- | --- |
| [@Regular_H1B_H4_VisaSlotsChecking](https://t.me/Regular_H1B_H4_VisaSlotsChecking) | H1/H4 in-person availability | High-signal moderation; joining may require admin approval |
| [@StrictlyH1_H4_regular_visa_slots](https://t.me/StrictlyH1_H4_regular_visa_slots) | H1/H4 regular slots | Active; contains both reports and questions; joining may require approval |
| [@h1b_slots](https://t.me/h1b_slots) | H1B/H4/L1/O1 | Public and active, but discussion can be noisy |
| [@VisaAppointmentsIndia](https://t.me/VisaAppointmentsIndia) | Multiple U.S. visa categories in India | Broad public fallback; verify the visa category carefully |

Do not copy IDs from another installation. Join a source yourself, review its
recent messages, run `visa-alert list-chats`, and add the ID shown by your own
Telegram session. A pending join request cannot be monitored until approved.

## Quality checklist

Prefer sources that:

- post current slot availability rather than predictions;
- distinguish H1B/H4, B1/B2, Dropbox/Interview Waiver, OFC/VAC, and consular slots;
- use clear city and month context;
- prohibit agents, paid booking offers, and direct-message solicitation;
- remain active without flooding members with unrelated discussion.

Avoid alerts that ask for payment, credentials, DS-160 access, one-time codes, or
remote-control access. Never give a group member a visa-site password or Telegram
login code. Confirm every report on the official appointment site yourself.

## Detector tuning

Test representative phrases before changing thresholds:

```powershell
visa-alert check "Bulk appointments Hyderabad Dec 2026"
visa-alert check "OFC available but no submit button"
visa-alert check "Any H1B dates for Dec"
visa-alert check "H1B slots available, low charges, ping me"
```

The first is a possible alert. The other three should remain LOW because they are
unbookable, questions, or promotional.
