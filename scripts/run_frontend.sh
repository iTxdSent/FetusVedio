#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${FRONTEND_HOST:-0.0.0.0}"
PORT="${FRONTEND_PORT:-5173}"
INSTALL_DEPS="${FRONTEND_INSTALL_DEPS:-0}"

if ! command -v node >/dev/null 2>&1; then
  echo "未检测到 node，请先安装 Node.js（建议 >= 20）。"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "未检测到 npm，请先安装 npm。"
  exit 1
fi

cd "${ROOT_DIR}/frontend"

if [[ ! -d node_modules ]]; then
  npm ci
elif [[ "${INSTALL_DEPS}" == "1" ]]; then
  npm install
fi

echo "启动前端: host=${HOST}, port=${PORT}"
npm run dev -- --host "${HOST}" --port "${PORT}"
