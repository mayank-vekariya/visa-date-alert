# How Visa Date Alert works

Visa Date Alert is a local, read-only listener. It signs in through Telegram's
client API as the user, watches only explicitly configured chats, scores each new
text message, and sends a separate private notification when the evidence is
strong enough.

```mermaid
flowchart LR
    A[Selected Telegram groups] --> B[Telethon listener]
    B --> C[Rule-based message detector]
    C -->|LOW| D[Ignore and log score]
    C -->|MEDIUM| E[Private alert bot]
    C -->|MEDIUM or HIGH| F[Saved Messages archive]
    C -->|HIGH and enabled| G[Twilio phone call]
    E --> H[Timed reminder]
```

## 1. Source boundary

`MONITORED_CHAT_IDS` is required and explicit. An empty value stops startup, so
the application cannot accidentally listen to every Telegram conversation. The
listener does not post, react, mark messages as read, scrape an entire account,
or automate the visa-booking website.

## 2. Detection

Message text is Unicode-normalized and compared with configurable visa aliases
and Indian consulate locations. The detector combines evidence instead of
alerting on one broad word:

- slot/open/available and bulk-appointment phrases;
- a target visa such as H1B, H4, Dropbox, B1/B2, or Interview Waiver;
- a target city or short code such as Hyderabad or HYD;
- urgency and appointment-month context.

Hard negatives stop common false alarms first: `NA`, no slots, already gone,
closed, past availability, questions, no submit button, and agent/promotional
messages. Configured aliases are matched as terms, so a short alias such as `IW`
does not match inside an unrelated word such as `preview`.

The score maps to three levels:

| Level | Default score | Result |
| --- | ---: | --- |
| LOW | 0–4 | Logged only |
| MEDIUM | 5–8 | Telegram bot + Saved Messages + reminders |
| HIGH | 9+ | Same alerts, plus a Twilio call when enabled |

The thresholds are configurable in `.env`.

## 3. Deduplication and privacy

SQLite stores the source chat ID, source message ID, timestamps, and SHA-256
fingerprints used to prevent repeats. Message bodies are not stored in the
database. Logs contain scoring metadata, not configured credentials.

The local Telegram `.session` file is sensitive because it represents an active
account login. It and `.env` are ignored by Git and must never be uploaded.

## 4. Alert delivery

The private companion bot produces normal Telegram notifications, including the
source title, original message, timestamp, confidence score, and original-message
link when Telegram exposes one. Saved Messages provides a personal archive.

Twilio is optional. Calls are created only for HIGH alerts and only when both
`ENABLE_CALLS=true` and all required Twilio settings are present. A public HTTPS
TwiML URL can be used when a trial account cannot retrieve inline TwiML.

## 5. Runtime

On Windows, `install-startup.ps1` creates a Scheduled Task that starts the monitor
at sign-in and restarts it after transient failures. A file lock prevents multiple
instances. The computer must remain awake and online.

## Limitations

- Telegram reports are crowd-sourced and can be wrong or late.
- Groups can change names, access rules, and message conventions.
- The monitor cannot reserve a slot and should never be given visa-site passwords.
- Phone calls and SMS may incur Twilio charges.
- This project is not affiliated with Telegram, Twilio, any embassy, or the U.S.
  Department of State.
