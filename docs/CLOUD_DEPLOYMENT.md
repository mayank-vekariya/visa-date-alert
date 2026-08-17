# Run Visa Date Alert continuously in the cloud

A small Linux virtual machine can keep the Telegram client connected while your
PC is off. The application uses outbound connections only, so it does not need a
public website, inbound application port, or public API.

## Current cost reality

There is no permanent cloud option this guide can honestly guarantee at $1–$2 per
month. Provider offers and account eligibility can change:

| Option | Current practical cost | Important limitation |
| --- | --- | --- |
| AWS EC2 | $0 initially for an eligible new account | Accounts created on or after July 15, 2025 use a [six-month Free Plan/credit model](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-free-tier-usage.html) |
| Google Compute Engine | Free eligible `e2-micro` compute, but roughly $3.60/month for the required public IPv4 | Google lists in-use VM IPv4 at [$0.005/hour](https://cloud.google.com/vpc/network-pricing#ipaddress); other usage can add cost |
| Oracle Cloud | Eligible Always Free compute includes a public IP | Oracle says [low-usage Always Free instances may be reclaimed](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm), which is risky for an urgent monitor |

For an eligible new account, AWS is the best short-term choice because its credits
can cover a small VM and public IPv4 for up to six months. For a stable long-term
installation, budget at least about $4/month and verify the provider's estimate
before creating anything. Create a $1 budget alert during any free period; budget
alerts notify you but do not necessarily stop resources.

## 1. Create the VM

For an eligible AWS Free Plan account, create an EC2 instance with:

- Ubuntu Server 24.04 LTS;
- a `t3.micro` instance type marked Free Tier eligible in the console;
- an 8 GB `gp3` root volume;
- an auto-assigned public IPv4 address;
- SSH (port 22) allowed only from **My IP**, with no HTTP/HTTPS rules.

The monitor needs outbound internet access but no inbound application port. Review
the console estimate, credit balance, and Free Tier eligibility before creating
the VM. The remaining Linux instructions also work on Google, Oracle, or another
Ubuntu VM.

## 2. Install the application

Open the VM's SSH terminal and run:

```bash
sudo apt-get update
sudo apt-get install -y git python3-venv
cd "$HOME"
git clone https://github.com/mayank-vekariya/visa-date-alert.git
cd visa-date-alert
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
cp .env.example .env
chmod 600 .env
nano .env
```

Fill `.env` with your own credentials and private chat IDs. Keep the Mumbai/New
Delhi rule values from `.env.example`. Never paste secrets into a Git commit,
support message, VM startup script, or public console screenshot.

## 3. Create a fresh Telegram session

Run this once in the SSH terminal:

```bash
.venv/bin/visa-alert doctor
.venv/bin/visa-alert list-chats
```

Telegram may send a login code to the existing Telegram app and may request the
account's two-step-verification password. This creates
`data/telegram_visa_monitor.session` on the VM. Treat that file like a password:
Telethon's [session documentation](https://docs.telethon.dev/en/stable/concepts/sessions.html)
explains that it contains enough authorization data to access the account.

Use a fresh server login instead of copying the Windows session database while it
is active. Never upload the session file to GitHub.

## 4. Test the exact rule without sending alerts

These commands do not connect to Telegram or call Twilio:

```bash
.venv/bin/visa-alert check "B1/B2 Slots Alert! Location: NEW DELHI OFC Available Dates: 1"
.venv/bin/visa-alert check "B1/B2 Slots Alert! Location: MUMBAI OFC Available Dates: 1"
.venv/bin/visa-alert check "B1/B2 Slots Alert! Location: HYDERABAD OFC Available Dates: 1"
```

The first two must be HIGH; Hyderabad must be LOW.

## 5. Install the Linux service and watchdog

The included installer expects the repository at `~/visa-date-alert`:

```bash
nano .env  # temporarily set DRY_RUN=true
chmod +x deploy/linux/install.sh deploy/linux/watchdog.sh
./deploy/linux/install.sh
```

It installs a user-level systemd service with automatic restart and a persistent
hourly heartbeat timer. User lingering keeps the service running after SSH logout
and starts it during VM boot.

Check it with:

```bash
systemctl --user status visa-date-alert.service
systemctl --user status visa-date-alert-health.timer
journalctl --user -u visa-date-alert.service -n 50 --no-pager
```

## 6. Switch over without duplicate calls

Keep the cloud copy in `DRY_RUN=true` while checking its service and heartbeat.
After it is healthy, stop and disable the Windows tasks:

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall-startup.ps1
```

Then on the cloud VM set `DRY_RUN=false` and reload it:

```bash
nano .env
systemctl --user restart visa-date-alert.service
```

Do not leave both live installations active. Each has independent deduplication
state, so one Telegram post could otherwise produce two notifications and two paid
Twilio calls.

To return to Windows later, stop the cloud service first:

```bash
systemctl --user disable --now visa-date-alert.service visa-date-alert-health.timer
```
