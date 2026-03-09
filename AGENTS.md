# AGENTS.md

## 项目名称
胎儿超声视频流实时解译系统（Demo）

## 项目目标
构建一个可运行的最小 Demo，支持：
1. 患者信息录入
2. 采集卡视频 / 本地视频切换
3. 实时视频显示
4. 切面分类结果展示
5. 分割结果与测量结果叠加展示
6. 自动留图、手动保存、历史查询

## 关键总原则
1. 只做 Demo，不做医院级产品。
2. 优先保证系统链路完整，而不是追求模型真实性能。
3. 本项目中的“切面分类模型”和“分割模型 + 测量后处理”在当前阶段**只允许实现为 Mock 组件**，不得在本阶段引入真实训练代码、真实 ONNX 推理或训练流程。
4. Mock 组件必须保留稳定、可替换的统一接口，后续可以在不改动前后端主流程的前提下替换为真实模型。
5. 后端统一使用 Python + FastAPI。
6. 前端统一使用 Vue 3 + TypeScript + Vite。
7. 数据库使用 SQLite。
8. 实时视频链路优先保证“显示帧与结果同步”，接受一定延迟。
9. 单用户、单会话、单采集源，不做并发隔离。
10. 所有界面文案、需求文档、验收说明使用中文；代码标识符、接口字段名、数据库字段名保持英文。
11. Python 环境隔离与包管理统一使用 Miniconda（Conda），禁止使用 venv/virtualenv/poetry/pipenv 作为项目标准方案。
12. Python 版本固定为 3.10.x（开发机与 Ubuntu 部署机保持一致）。

## Mock 约束（非常重要）
1. 分类模块只输出模拟分类结果：
   - OTHER / BV / AAV / 3VT
2. 分割模块只输出模拟 mask 或模拟轮廓数据。
3. 测量模块只输出模拟测量值，但字段必须符合切面契约：
   - BV: SVC, IVC
   - AAV: AAo, TA, Isthmus, DAo
   - 3VT: DA, DAo
4. Mock 结果应当具备“可重复、可调试、可演示”特点：
   - 可以基于帧序号轮换切面类别
   - 可以固定输出某些测量值
   - 可以伪造成功/失败状态
5. 所有模型相关逻辑必须通过接口或适配器隔离：
   - ClassifierProvider
   - SegmentationProvider
   - MeasurementProvider
6. 任何阶段都不要把真实模型文件作为项目必须依赖。
7. 不要为了接 Mock 而把接口写死到某个具体模型格式。

## 代码修改原则
1. 改动要最小、清晰、可回滚。
2. 每个阶段只完成对应 SPEC 规定的内容，不跨阶段堆功能。
3. 提交的代码必须能本地启动，至少满足阶段验收标准。
4. 生成代码时先复用已有目录和模块，不要重复造轮子。
5. 如果某功能缺少真实模型依赖，则必须先提供 Mock 版本并把替换点写清楚。

## 建议的模型接口
```python
class ClassifierProvider:
    def predict(self, frame_bgr) -> dict:
        ...
        # 返回:
        # {
        #   "plane": "BV",
        #   "confidence": 0.91,
        #   "class_id": 1
        # }

class SegmentationProvider:
    def predict(self, frame_bgr, plane: str) -> dict:
        ...
        # 返回:
        # {
        #   "success": True,
        #   "mask": ...,
        #   "labels": [0, 1, 2]
        # }

class MeasurementProvider:
    def measure(self, frame_bgr, plane: str, mask) -> dict:
        ...
        # 返回:
        # {
        #   "success": True,
        #   "metrics": {...},
        #   "qc": {...}
        # }
```

## 当前阶段执行方式
1. 先读取 `specs/00-系统基线.SPEC.md`
2. 再读取当前阶段对应的 `SPEC.md`
3. 如有需要，再读取 `.agents/skills/阶段X-.../SKILL.md`
4. 仅按当前阶段输出代码、测试、说明，不提前实现后续阶段内容
