# Contributing

Thanks for improving Visa Date Alert. Keep contributions focused on reliable,
read-only monitoring and safe personal notifications.

## Development setup

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\ruff.exe check .
```

Detector changes should include examples for both the desired alert and likely
false positives. Tests must never use live Telegram or Twilio credentials.

## Pull requests

- Explain the behavior change and its safety impact.
- Add or update tests.
- Never commit `.env`, session files, phone numbers, private chat IDs, logs, or
  copied private messages.
- Keep the monitor read-only. Features that post to source groups, automate visa
  websites, bypass rate limits, or book appointments are out of scope.
