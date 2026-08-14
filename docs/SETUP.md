# Complete setup guide

This guide creates a local Telegram listener, a separate notification bot, and an
optional Twilio HIGH-alert call. No secret belongs in GitHub.

## Prerequisites

- Windows 10 or 11
- Python 3.11 or newer
- a Telegram account with access to the source groups
- optional: a Twilio account and voice-capable number

## 1. Install the project

```powershell
git clone https://github.com/mayank-vekariya/visa-date-alert.git
Set-Location .\visa-date-alert
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

`setup.ps1` creates `.venv`, installs the package, and copies `.env.example` to
the ignored local file `.env`.

## 2. Create Telegram API credentials

1. Sign in at [my.telegram.org](https://my.telegram.org/).
2. Open **API development tools**.
3. Create an application. The title/description can be personal; choose Desktop
   or Other as the platform.
4. Copy `api_id` and `api_hash` into `.env`.
5. Add the account phone number with country code to `TELEGRAM_PHONE`.

These credentials belong to the personal Telegram client, not the notification
bot. Never publish the API hash or `data/*.session`.

## 3. Create the companion alert bot

1. Open Telegram's verified [@BotFather](https://t.me/BotFather).
2. Send `/newbot`, choose a name and username, and copy the token to
   `TELEGRAM_ALERT_BOT_TOKEN`.
3. Open the new bot and send `/start`.
4. Run:

   ```powershell
   .\.venv\Scripts\visa-alert.exe find-alert-chat
   ```

5. Copy the displayed private chat ID to `TELEGRAM_ALERT_CHAT_ID`.

The token is read from `.env` and is never printed by the command.

## 4. Select source groups

Join each desired group manually in Telegram first. Then run:

```powershell
.\.venv\Scripts\visa-alert.exe list-chats
```

Copy only the desired numeric IDs into `MONITORED_CHAT_IDS`, comma-separated.
Keep that value blank in `.env.example`; personal chat IDs should stay local.
See [source selection](SOURCE_SELECTION.md) for quality and scam checks.

## 5. Choose visas and locations

The defaults cover B1/B2 and H1B/H4 terminology used in Indian appointment
groups. Values are comma-separated and case-insensitive:

```dotenv
TARGET_VISAS=B1/B2,B1 B2,visitor visa,tourist visa,H1B,H-1B,H1,H4,Dropbox,Interview Waiver,IW
TARGET_LOCATIONS=Mumbai,Delhi,Hyderabad,Chennai,Kolkata,MUM,DEL,HYD,CHN,KOL
MEDIUM_SCORE=5
HIGH_SCORE=9
```

## 6. Verify safely

The doctor never displays secrets or sends an alert:

```powershell
.\.venv\Scripts\visa-alert.exe doctor
.\.venv\Scripts\visa-alert.exe check "H1B slots available in Hyderabad for December. Check now"
.\.venv\Scripts\visa-alert.exe check "NA 2 All"
```

For a live listening trial with no notifications or calls, set `DRY_RUN=true`,
run the monitor, and inspect `logs/visa-alert.log`. Restore `DRY_RUN=false` when
ready.

## 7. Optional Twilio calls

Fill these local values only after Telegram alerts work:

```dotenv
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
ALERT_TO_NUMBER=
TWILIO_TWIML_URL=
ENABLE_CALLS=false
ENABLE_SMS=false
```

Trial accounts often require the destination phone to be verified and play a
trial announcement before the custom voice message. If Twilio says it cannot
reach the TwiML server, create a public HTTPS TwiML Bin/Twimlet and place its URL
in `TWILIO_TWIML_URL`. A minimal response is:

```xml
<Response>
  <Say>Urgent visa alert. Check Telegram immediately.</Say>
  <Pause length="1" />
  <Say>Repeat. Urgent visa alert. Check Telegram now.</Say>
</Response>
```

Set `ENABLE_CALLS=true` only after the voice URL works. Calls are reserved for
HIGH alerts; detector tests and `doctor` never call Twilio.

## 8. Start at Windows sign-in

```powershell
powershell -ExecutionPolicy Bypass -File .\install-startup.ps1
Get-ScheduledTask -TaskName "Visa Date Alert Monitor"
```

To remove only the startup task while keeping all local data:

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall-startup.ps1
```

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Login code never arrives | Telegram often sends it inside Telegram before SMS |
| Group is missing | Finish its join approval, then rerun `list-chats` |
| Bot notifications are silent | Unmute the private bot chat in Telegram |
| `No bot chats found` | Send `/start` to the companion bot, then retry |
| Monitor exits immediately | Run `visa-alert doctor` and inspect the last log lines |
| Twilio cannot reach server | Use a public HTTPS TwiML URL, not localhost |
| A second monitor will not start | Expected: the singleton lock prevents duplicates |

Run automated verification with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
