# frontend

## 启动

```bash
cd /Users/sent/FetusVedio
./scripts/run_frontend.sh
```

默认地址：`http://127.0.0.1:5173`

联调前请先按后端文档创建并激活 Miniconda Python 3.10 环境，再启动后端服务。

可选脚本参数（环境变量）：
1. `FRONTEND_HOST`（默认 `0.0.0.0`）
2. `FRONTEND_PORT`（默认 `5173`）
3. `FRONTEND_INSTALL_DEPS`（默认 `0`，设为 `1` 可强制执行 `npm install`）

说明：首次运行若 `node_modules` 不存在，会自动执行 `npm ci`。

可选环境变量：
1. `VITE_API_BASE_URL`，默认 `http://127.0.0.1:8000/api/v1`
2. `VITE_WS_URL`，默认 `ws://127.0.0.1:8000/ws/stream`
3. `VITE_MEDIA_BASE_URL`，默认从 `VITE_API_BASE_URL` 推导
4. 示例文件：[frontend/.env.example](/Users/sent/FetusVedio/frontend/.env.example)

实时页“选择本地视频”按钮会打开系统文件选择器（Finder/文件管理器），选中文件后自动上传到后端并切换视频源。

实时测量页右侧提供“留图预览”：
1. 默认显示当前患者最新留图。
2. 支持通过“选择留存图片”在该患者历史留图中切换预览。

登录要求：
1. 未登录无法进入患者/实时/历史页面。
2. 登录后可进行患者录入与实时测量。

完整 Ubuntu 部署与联调验收见：
1. [/Users/sent/FetusVedio/docs/06-部署联调与Demo验收.md](/Users/sent/FetusVedio/docs/06-部署联调与Demo验收.md)
