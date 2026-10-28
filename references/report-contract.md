# Printability 报告契约

## 必填结论

```yaml
model: <绝对路径或对象/版本>
intent: solid | surface | multipart | unknown
functional_intent: [<route id>, ...] | unknown
process: fdm | resin | powder | metal | unknown
geometry_gate: pass | fail | unknown
process_feasibility: pass | fail | conditional | unknown
functional_validation: pass | fail | conditional | not_applicable | unknown
quality_risk: low | medium | high | unknown
evidence_level: static | source | sliced | physical
```

不要生成综合分数。任何硬阻断都保持可见，不能被其他通过项平均掉。

## 状态含义

- `geometry_gate: pass`：当前意图下，已执行的几何门禁未发现阻断。它不是切片或实物通过。
- `geometry_gate: fail`：存在有证据的几何阻断；列出具体位置/数量和证据。
- `process_feasibility: pass`：目标配置已实际切片并检查相关层，未发现工艺阻断。仅凭静态网格不得使用。
- `process_feasibility: conditional`：可继续，但依赖方向、支撑、配置、修复或试片。
- `functional_validation: pass`：用户要求的功能已按对应路由取得足够证据；纯静态网格检查不得使用。
- `functional_validation: fail`：存在有证据的功能失败，例如装配干涉、活动件锁死、接口缺失、流路不通或实测不合格。
- `functional_validation: conditional`：功能依赖尚未锁定的材料、方向、间隙、五金、后处理、装配或试打结果。
- `functional_validation: not_applicable`：已确认模型没有装配、运动、配合、容纳、流体或其他功能要求。未知用途不能使用此状态。
- `quality_risk`：相对于用户目标评估。没有表面/尺寸/功能要求时为 `unknown`，不要默认 `low`。

## 发现项格式

每个发现项包含：

```yaml
- id: G-01
  class: blocker | process_risk | quality_risk | unknown
  check: <检查项>
  evidence: <工具、数值、层号、视图或实测>
  impact: <为什么影响打印或结果>
  next_action: <最小修复或验证>
  revalidate: static | source | sliced | physical
```

## 推荐报告顺序

1. 五轴结论、功能意图路由与证据层级。
2. 硬阻断。
3. 工艺风险。
4. 质量/功能风险。
5. 未检查和未知参数。
6. 最小下一步，例如修一个洞、换方向重切、做局部试片，而不是泛泛地说“优化模型”。

若执行了自动修复，增加修复前后差异表，并同时保留原模型结论。
