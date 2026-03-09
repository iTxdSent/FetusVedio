#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${CONDA_ENV_NAME:-fetus_video_demo_py310}"
HOST="${BACKEND_HOST:-0.0.0.0}"
PORT="${BACKEND_PORT:-8000}"
RELOAD="${BACKEND_RELOAD:-0}"

if ! command -v conda >/dev/null 2>&1; then
  echo "未检测到 conda，请先安装 Miniconda。"
  exit 1
fi

if ! conda env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
  echo "未找到 conda 环境: ${ENV_NAME}"
  echo "请先执行: ./scripts/setup_conda_env.sh"
  exit 1
fi

EXTRA_ARGS=()
if [[ "${RELOAD}" == "1" ]]; then
  EXTRA_ARGS+=(--reload)
fi

cd "${ROOT_DIR}/backend"
echo "启动后端: env=${ENV_NAME}, host=${HOST}, port=${PORT}, reload=${RELOAD}"
conda run -n "${ENV_NAME}" uvicorn app.main:app --host "${HOST}" --port "${PORT}" "${EXTRA_ARGS[@]}"
