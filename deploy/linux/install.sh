#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
expected_root="${HOME}/visa-date-alert"
unit_directory="${HOME}/.config/systemd/user"

if [[ "${project_root}" != "${expected_root}" ]]; then
  echo "Clone the repository at ${expected_root}, then run this installer again." >&2
  exit 1
fi

if [[ ! -f "${project_root}/.env" ]]; then
  echo "Missing .env. Copy .env.example, fill it in, and run doctor first." >&2
  exit 1
fi

if [[ ! -x "${project_root}/.venv/bin/visa-alert" ]]; then
  echo "Missing Linux virtual environment. Follow docs/CLOUD_DEPLOYMENT.md first." >&2
  exit 1
fi

install -d -m 0700 "${unit_directory}"
install -m 0600 "${project_root}/deploy/linux/visa-date-alert.service" "${unit_directory}/"
install -m 0600 "${project_root}/deploy/linux/visa-date-alert-health.service" "${unit_directory}/"
install -m 0600 "${project_root}/deploy/linux/visa-date-alert-health.timer" "${unit_directory}/"

sudo loginctl enable-linger "${USER}"
systemctl --user daemon-reload
systemctl --user enable --now visa-date-alert.service
systemctl --user enable --now visa-date-alert-health.timer

echo "Visa Date Alert is installed as a persistent Linux user service."
echo "Run: systemctl --user status visa-date-alert.service"
