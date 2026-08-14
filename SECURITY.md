# Security policy

Visa Date Alert handles credentials that can access a Telegram account and, when
enabled, a Twilio account. Treat the local `.env` and `data/*.session` files like
passwords.

## Supported version

Security fixes are made on the latest version on the default branch.

## Report a vulnerability

Please use a private [GitHub security advisory](https://github.com/mayank-vekariya/visa-date-alert/security/advisories/new).
Do not paste tokens, session files, phone numbers, chat IDs, or private Telegram
messages into a public issue.

## If a secret was exposed

1. Revoke the BotFather token with `/revoke` and create a replacement.
2. Revoke affected Telegram sessions from **Settings → Devices**.
3. Rotate the Twilio Auth Token in the Twilio Console.
4. Remove the secret from the Git history; deleting only the latest copy is not
   sufficient.
5. Replace the local values and restart the monitor.

The repository intentionally ignores `.env`, Telegram session databases, the
deduplication database, and logs. CI uses no live credentials.
