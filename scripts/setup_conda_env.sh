#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="fetus_video_demo_py310"
ENV_FILE="backend/environment.yml"

if ! command -v conda >/dev/null 2>&1; then
  echo "未检测到 conda，请先安装 Miniconda。"
  exit 1
fi

if conda env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
  echo "检测到已存在环境: ${ENV_NAME}，执行更新..."
  conda env update -n "${ENV_NAME}" -f "${ENV_FILE}" --prune
else
  echo "创建环境: ${ENV_NAME}"
  conda env create -f "${ENV_FILE}"
fi

echo "完成。请执行: conda activate ${ENV_NAME}"
