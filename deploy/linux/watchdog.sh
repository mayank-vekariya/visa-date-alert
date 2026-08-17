#!/usr/bin/env bash
set -euo pipefail

project_root="${HOME}/visa-date-alert"
heartbeat_path="${project_root}/data/monitor.heartbeat"
service_name="visa-date-alert.service"
max_age_seconds=600

restart_monitor() {
  systemctl --user restart "${service_name}"
  sleep 10
}

if ! systemctl --user is-active --quiet "${service_name}"; then
  restart_monitor
fi

if [[ ! -f "${heartbeat_path}" ]]; then
  restart_monitor
fi

now_epoch="$(date +%s)"
heartbeat_epoch="$(stat -c %Y "${heartbeat_path}")"
heartbeat_age="$((now_epoch - heartbeat_epoch))"
if (( heartbeat_age > max_age_seconds )); then
  restart_monitor
fi

if ! systemctl --user is-active --quiet "${service_name}"; then
  echo "Visa Date Alert is not running after recovery." >&2
  exit 1
fi

now_epoch="$(date +%s)"
heartbeat_epoch="$(stat -c %Y "${heartbeat_path}")"
heartbeat_age="$((now_epoch - heartbeat_epoch))"
if (( heartbeat_age > max_age_seconds )); then
  echo "Visa Date Alert heartbeat is still stale after recovery." >&2
  exit 1
fi

echo "Visa Date Alert is healthy; heartbeat age is ${heartbeat_age}s."
