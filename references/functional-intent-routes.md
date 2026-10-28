# 功能意图检查路由

本页把模型用途映射为 Printability 的功能检查，不把“水密并能切片”误写成“成品可用”。路由参考 Hi3D Agent 公开的 [3D Printing Skills 分类](https://www.hi3d.ai/agent?category=3d-printing)及各 Skill 公开简介，核对日期为 2026-10-28。它们是公开任务分类提供的检查启发，不代表 Hi3D 的内部提示词、实现或验证标准，也不表示本 Skill 与 Hi3D 有隶属关系。

不得因引用本页自动打开 Hi3D、上传模型或发送任务。只有用户明确要求使用 Hi3D 时，才能进行外部交互。

## 路由选择

先根据用户用途、源 CAD 语义和零件关系选择一个或多个路由。用途不明时标为 `unknown` 并询问/列出最小必要信息；不要从外形猜功能。Hi3D Skill 名称只用于说明公开灵感来源，报告使用本页的 Printability 路由 ID。

| Printability 路由 | 对应的公开 Hi3D Skill | 主要检查 |
| --- | --- | --- |
| `general-product` | [`product-design`](https://www.hi3d.ai/agent/skills/product-design?category=3d-printing) | 载荷路径、结构连续性、制造拆分、关键尺寸与交付文件一致性。 |
| `split-assembly` | [`print-kit`](https://www.hi3d.ai/agent/skills/print-kit?category=3d-printing)、[`image-to-assembly`](https://www.hi3d.ai/agent/skills/image-to-assembly?category=3d-printing)、[`multiview-parts`](https://www.hi3d.ai/agent/skills/multiview-parts?category=3d-printing) | 拆件边界、连接器、定位、防呆、装配顺序、公差、零件遗漏与视图歧义。 |
| `motion-joint` | [`print-joints`](https://www.hi3d.ai/agent/skills/print-joints?category=3d-printing)、[`articulated-sculpture`](https://www.hi3d.ai/agent/skills/articulated-sculpture?category=3d-printing)、[`twisty-fidget`](https://www.hi3d.ai/agent/skills/twisty-fidget?category=3d-printing)、[`motion-base`](https://www.hi3d.ai/agent/skills/motion-base?category=3d-printing) | 活动间隙、打印后释放、运动范围、限位、摩擦、捕获件、轮轴与重复寿命。 |
| `fit-enclosure` | [`device-enclosure`](https://www.hi3d.ai/agent/skills/device-enclosure?category=3d-printing)、[`phone-case-relief`](https://www.hi3d.ai/agent/skills/phone-case-relief?category=3d-printing)、[`frame-design`](https://www.hi3d.ai/agent/skills/frame-design?category=3d-printing) | 实测基准、净空、壁厚、端口/按钮/镜头开口、卡扣或紧固件、装拆路径、挂装/站立稳定性。 |
| `lamp-system` | [`lamp-design`](https://www.hi3d.ai/agent/skills/lamp-design?category=3d-printing) | 灯具装配、走线、光学遮挡、散热、阻燃/绝缘需求、光源和五金净空；电气安全必须另行验证。 |
| `hollow-container` | [`vase-design`](https://www.hi3d.ai/agent/skills/vase-design?category=3d-printing)、[`sculpture-container`](https://www.hi3d.ai/agent/skills/sculpture-container?category=3d-printing)、[`relief-box`](https://www.hi3d.ai/agent/skills/relief-box?category=3d-printing) | 内腔连通、开口可达、底部稳定、壁厚、盖体配合、困液/困粉、清洁与实际密封要求。 |
| `fluid-path` | [`teapot-design`](https://www.hi3d.ai/agent/skills/teapot-design?category=3d-printing)、[`water-feature`](https://www.hi3d.ai/agent/skills/water-feature?category=3d-printing) | 流路连通、入口/出口、泵腔、虹吸/回流、排液、死角、泄漏、清洁和材料接触安全。 |
| `threaded-closure` | [`screw-bottle`](https://www.hi3d.ai/agent/skills/screw-bottle?category=3d-printing) | 内外螺纹匹配、导入角、根部强度、打印方向、装配余量、止挡、密封面与循环开合。 |
| `relief-surface` | [`relief-brush`](https://www.hi3d.ai/agent/skills/relief-brush?category=3d-printing)、[`phone-case-relief`](https://www.hi3d.ai/agent/skills/phone-case-relief?category=3d-printing) | 浮雕是否为真实几何、最小凸起/凹槽、基体壁厚、曲面贴合、采样/三角化和方向性表面损失。 |
| `subtractive-layered` | [`layered-laser-ornament`](https://www.hi3d.ai/agent/skills/layered-laser-ornament?category=3d-printing) | 这是激光切割/层叠意图，不沿用增材水密门禁；改查闭合轮廓、切缝补偿、材料厚度、桥接、层序和装配。 |

20 个公开 Skill 均已覆盖；`phone-case-relief` 同时属于外壳配合和浮雕表面，其他模型也可组合路由。

## 各路由的最低证据

### `general-product`

- 源设计：关键尺寸、载荷、接触面、紧固件与材料假设有记录。
- 切片：关键薄弱截面和连接处没有被路径省略；方向与主要受力相容。
- 实物：承载、尺寸或寿命要求存在时，用试件或成品测试；没有测试不得写功能通过。

### `split-assembly`

- 每个零件有唯一身份、数量和方向；不存在从多视图推断而未确认的隐藏结构。
- 检查装配顺序、工具可达性、防呆、连接器根部强度、配合类型和材料/工艺相关余量。
- 在切片中检查接口是否保留；最终通过通常需要打印配合试片或完成一次装配。

### `motion-joint`

- 在源设计中做全行程干涉检查，确认限位和捕获关系。
- 检查首层膨胀、支撑粘连、粉末/树脂残留是否会锁死活动间隙。
- 打印后验证释放方法、活动范围、松紧、重复循环和预期载荷；仅能转动一次不等于寿命通过。

### `fit-enclosure`

- 输入必须来自实测尺寸或可信规格，记录测量基准和公差，不能只凭图片比例。
- 检查端口、按钮、镜头、通风、螺钉柱、卡扣、盖体和装拆路径；浮雕不得侵入功能净空。
- 用关键截面和试装验证配合；柔性外壳还需材料硬度、回弹和壁厚证据。

### `lamp-system`

- 分离机械 Printability 与电气/热安全结论。验证灯座、光源、电源、走线、应力释放、散热和维护可达性。
- 对温升、阻燃、绝缘和市电安全没有合格证据时，`functional_validation` 只能是 `conditional` 或 `unknown`。

### `hollow-container`

- 检查腔体、盖体、开口与清洁工具是否可达，排液/排粉通道是否真实连通。
- “水密网格”不是“成品防水”。盛液、密封或食品接触用途需要材料、工艺、后处理和泄漏/卫生测试。

### `fluid-path`

- 在源模型中确认完整流路、最低点排液、泵和管路接口、溢流路径及死角。
- 切片检查内壁、支撑和困液/吸盘风险；实物做流量、泄漏、回流、噪声和清洁测试。
- 饮用或食品接触必须另行核对材料与法规；本 Skill 不替代合规认证。

### `threaded-closure`

- 比较内外螺纹的牙型、螺距、旋向、有效啮合长度、导入、止挡和打印后余量。
- 切片确认牙顶/牙根没有消失；先打印短配合试片，再验证扭矩、循环和密封。

### `relief-surface`

- 确认图案已成为实体几何，而非仅材质、凹凸或法线贴图。
- 以目标方向和实际路径/像素检查最小凸起、凹槽、文字与曲率贴合；评估支撑痕和三角化分面。

### `subtractive-layered`

- 把对象从增材门禁移交给激光切割/层叠检查；不得因为二维轮廓不是水密体积而判失败。
- 验证轮廓闭合、重复线、最小桥宽、切缝补偿、材料厚度、纹理方向、层序、定位与胶合/连接方式。

## 状态规则

- 仅运行 `scripts/audit_mesh.py`：`functional_validation: unknown`。
- 已确认无功能要求：`not_applicable`。
- 完成源设计检查但仍依赖切片或试打：通常为 `conditional`。
- 发现确定干涉、接口遗漏、流路断开或尺寸不匹配：`fail`。
- 只有对应需求已由足够的 `source`、`sliced` 或 `physical` 证据覆盖时才用 `pass`，并在发现项中写明证据。
