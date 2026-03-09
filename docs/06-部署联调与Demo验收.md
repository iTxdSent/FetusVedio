# 06 阶段：部署、联调与 Demo 验收

## 1. 适用范围
1. 本文用于 Ubuntu Demo 环境部署与联调。
2. 模型模式默认 `Mock`，不依赖真实模型文件。
3. Python 环境统一使用 Miniconda，版本固定 `3.10.x`。

## 2. 环境前置
1. 已安装 Miniconda（Ubuntu）。
2. 已安装 Node.js（建议 `>=20`）与 npm。
3. 已安装 Git。

可选自检：
```bash
conda --version
node -v
npm -v
```

## 3. 拉取代码
```bash
cd /path/to/workspace
git clone <your-repo-url> FetusVedio
cd FetusVedio
```

## 4. 创建与验证 Conda 环境（Python 3.10）
```bash
./scripts/setup_conda_env.sh
conda activate fetus_video_demo_py310
python --version
python -c "import fastapi, cv2, sqlalchemy; print('backend deps ok')"
```

期望输出：`Python 3.10.x`。  
环境定义文件：`backend/environment.yml`。

## 5. 配置文件说明

### 5.1 后端配置（`backend/.env`）
```bash
cp backend/.env.example backend/.env
```

核心配置项：
1. `DATABASE_URL`：SQLite 地址（默认指向 `backend/data/app.db`）。
2. `STREAM_FPS`：推流目标帧率（默认 30）。
3. `CAPTURE_DEVICE_INDEX`：采集卡设备索引（默认 0）。
4. `LOCAL_VIDEO_UPLOAD_DIR`：本地视频上传目录。
5. `SNAPSHOT_ROOT_DIR`：留图目录。
6. `MODEL_PROVIDER_BACKEND`：模型后端，当前应为 `mock`。
7. `AUTO_CAPTURE_CONSECUTIVE_FRAMES`：自动留图连续帧阈值。
8. `AUTO_CAPTURE_COOLDOWN_SEC`：同切面自动留图冷却时间。

### 5.2 前端配置（`frontend/.env.local`）
```bash
cp frontend/.env.example frontend/.env.local
```

配置项：
1. `VITE_API_BASE_URL`：后端 API 根地址。
2. `VITE_WS_URL`：实时帧 WebSocket 地址。
3. `VITE_MEDIA_BASE_URL`：媒体文件地址前缀（可选）。

## 6. 启动脚本

### 6.1 启动后端
```bash
./scripts/run_backend.sh
```

可选环境变量：
1. `CONDA_ENV_NAME`（默认 `fetus_video_demo_py310`）
2. `BACKEND_HOST`（默认 `0.0.0.0`）
3. `BACKEND_PORT`（默认 `8000`）
4. `BACKEND_RELOAD`（默认 `0`，开发期可设为 `1`）

### 6.2 启动前端
```bash
./scripts/run_frontend.sh
```

可选环境变量：
1. `FRONTEND_HOST`（默认 `0.0.0.0`）
2. `FRONTEND_PORT`（默认 `5173`）
3. `FRONTEND_INSTALL_DEPS`（默认 `0`，设为 `1` 可强制执行 `npm install`）

说明：
1. 若 `frontend/node_modules` 不存在，脚本会自动执行 `npm ci`。

## 7. 联调步骤（推荐）
1. 打开后端：`http://127.0.0.1:8000/api/v1/health`，确认 `{"status":"ok"}`。
2. 打开前端：`http://127.0.0.1:5173`。
3. 注册并登录用户。
4. 录入患者信息并进入实时测量页。
5. 输入比例尺并点击确定。
6. 点击开始检查，观察实时画面与切面/测量结果。
7. 使用“留图”按钮手动保存。
8. 切换“选择本地视频”，确认视频源切换正常。
9. 进入历史记录页，按患者 ID 查询并验证留图可见。

## 8. Mock 运行模式说明
1. 当前默认 `MODEL_PROVIDER_BACKEND=mock`。
2. Mock 分类只输出 `OTHER/BV/AAV/3VT`。
3. Mock 分割输出模拟 mask/轮廓，Mock 测量输出契约字段。
4. 没有真实模型文件时，系统也应可完成全链路演示。

## 9. Demo 验收清单
1. 无真实模型文件时，前后端可正常启动。
2. 可注册/登录，未登录无法访问主功能。
3. 可录入患者并开始检查。
4. 比例尺未确认前无法开始检查。
5. 实时视频、切面结果、测量值可展示。
6. 自动留图与手动留图均可用。
7. 历史查询可按患者 ID 返回留图记录与图片。
8. 本地视频输入与采集卡恢复切换可用。

## 10. 真实模型替换文档
见：`docs/06-Mock迁移到真实模型说明.md`
