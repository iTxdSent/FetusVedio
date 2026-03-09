# backend

## 启动

```bash
cd /Users/sent/FetusVedio
./scripts/setup_conda_env.sh
./scripts/run_backend.sh
```

健康检查：`GET http://127.0.0.1:8000/api/v1/health`

可选参数（通过环境变量）：
1. `CONDA_ENV_NAME`（默认 `fetus_video_demo_py310`）
2. `BACKEND_HOST`（默认 `0.0.0.0`）
3. `BACKEND_PORT`（默认 `8000`）
4. `BACKEND_RELOAD`（默认 `0`）

## 环境说明
1. Python 环境统一由 Miniconda 管理。
2. Python 版本固定为 `3.10.x`。
3. 依赖定义文件为 [environment.yml](/Users/sent/FetusVedio/backend/environment.yml)。
4. Ubuntu 部署/联调/验收文档见：
   - [/Users/sent/FetusVedio/docs/06-部署联调与Demo验收.md](/Users/sent/FetusVedio/docs/06-部署联调与Demo验收.md)
   - [/Users/sent/FetusVedio/docs/06-Mock迁移到真实模型说明.md](/Users/sent/FetusVedio/docs/06-Mock迁移到真实模型说明.md)

## 实时流接口（02阶段）
1. WebSocket 推流：`ws://127.0.0.1:8000/ws/stream`
2. 会话状态：`GET /api/v1/stream/state`
3. 开始/结束检查：`POST /api/v1/stream/start`、`POST /api/v1/stream/end`
4. 冻结/解冻：`POST /api/v1/stream/freeze`、`POST /api/v1/stream/unfreeze`
5. 上传并切换本地视频：`POST /api/v1/stream/upload-local-video`（multipart/form-data，字段 `file`）
6. 切换本地视频（路径模式）：`POST /api/v1/stream/switch-local-video`
7. 恢复采集卡：`POST /api/v1/stream/resume-capture`
8. 设置比例尺：`POST /api/v1/stream/spacing`（`spacing_cm_per_pixel`，单位 cm/px）

## 登录与鉴权
1. 注册：`POST /api/v1/auth/register`
2. 登录：`POST /api/v1/auth/login`
3. 当前用户：`GET /api/v1/auth/me`
4. 退出：`POST /api/v1/auth/logout`
5. 主功能接口（patients/stream/history）必须携带 `Authorization: Bearer <token>`。
6. `ws://.../ws/stream` 需要查询参数 `token`，未登录会被拒绝。

## FPS 说明
1. 默认目标 FPS 为 `30`（配置项 `STREAM_FPS`）。
2. 可通过 `.env` 覆盖，例如：`STREAM_FPS=24`。

## Provider 架构（04阶段）
1. 统一接口定义：`app/services/providers/base.py`
2. 默认 Mock 实现：
   - `app/services/providers/mock_classifier.py`
   - `app/services/providers/mock_segmentation.py`
   - `app/services/providers/mock_measurement.py`
3. Provider 选择入口：`app/services/providers/registry.py`
4. 配置切换项：`MODEL_PROVIDER_BACKEND`（当前仅支持 `mock`）
5. 未来接入真实模型时，只需新增 `Real*Provider` 并更新 `registry.py`，无需改控制器和前端接口。

## 数据持久化与历史（05阶段）
1. 数据表：
   - `patients`
   - `sessions`
   - `measurements`
   - `snapshots`
2. 自动留图规则：
   - `plane != OTHER`
   - `measurement.success = true`
   - 切面必填测量字段完整
   - 连续 2 帧满足条件（可配置）
   - 同切面 5 秒内不重复留图（可配置）
   - 仅在比例尺确认后可开始检查；测量值按 `像素值 * 比例尺(cm/px) * 10` 转换为 `mm`
3. 自动留图文件保存：
   - `raw.jpg`
   - `overlay.jpg`
   - `result.json`
4. 手动保存接口：`POST /api/v1/stream/manual-save`
5. 历史查询接口：
   - `GET /api/v1/history/patients/{patient_id}/snapshots`
   - `GET /api/v1/history/patients/{patient_id}/latest-snapshot`
