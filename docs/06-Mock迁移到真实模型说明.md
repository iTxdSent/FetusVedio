# 06 阶段：Mock 迁移到真实模型说明

## 1. 当前 Mock 结构
Provider 接口与默认实现：
1. 接口定义：`backend/app/services/providers/base.py`
2. Mock 分类：`backend/app/services/providers/mock_classifier.py`
3. Mock 分割：`backend/app/services/providers/mock_segmentation.py`
4. Mock 测量：`backend/app/services/providers/mock_measurement.py`
5. 组装入口：`backend/app/services/providers/registry.py`

## 2. 替换目录与文件
建议新增真实实现文件（示例命名）：
1. `backend/app/services/providers/real_classifier.py`
2. `backend/app/services/providers/real_segmentation.py`
3. `backend/app/services/providers/real_measurement.py`

模型权重/配置建议放在：
1. `backend/models/`（权重、推理配置）
2. `backend/configs/model/`（可选，模型配置文件）

## 3. 必须替换的 Provider
1. `ClassifierProvider.predict(frame_bgr) -> ClassificationResult`
2. `SegmentationProvider.predict(frame_bgr, plane) -> SegmentationResult`
3. `MeasurementProvider.measure(frame_bgr, plane, mask) -> MeasurementResult`

要求：
1. 输出字段必须保持当前契约（plane/confidence/metrics/qc 等）。
2. 切面测量字段保持不变：
   - BV: `SVC, IVC`
   - AAV: `AAo, TA, Isthmus, DAo`
   - 3VT: `DA, DAo`

## 4. 需要修改的模块
只需改两处：
1. 新增真实 Provider 文件。
2. 更新 `backend/app/services/providers/registry.py`，根据 `MODEL_PROVIDER_BACKEND` 返回真实 ProviderBundle。

## 5. 不需要改动的模块
以下模块保持不变：
1. 前端全部页面与 API 调用层（`frontend/src/**`）。
2. FastAPI 路由层（`backend/app/api/routes/**`）。
3. 会话状态、推流主循环与留图链路（`backend/app/services/realtime/**` 主流程）。
4. 数据持久化与历史查询（`backend/app/services/persistence.py`、`history` 路由）。

## 6. 配置切换方式
`backend/.env`：
```env
MODEL_PROVIDER_BACKEND=mock
```

接入真实模型后示例：
```env
MODEL_PROVIDER_BACKEND=real
```

同时在 `registry.py` 增加 `real` 分支即可。

## 7. 迁移后最小验证
1. `/api/v1/health` 正常。
2. WebSocket 可持续输出帧和推理结果。
3. 前端实时页可展示切面、测量、留图。
4. 自动留图与历史查询仍可用。
