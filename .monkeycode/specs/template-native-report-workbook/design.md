# 模板原生通报工作簿技术设计

Feature Name: template-native-report-workbook
Updated: 2026-08-19

## 1. 设计结论

样例工作簿采用“通报页引用明细页”的模板原生模式：

- `模版` Sheet：12 列、21 行，包含合并表头、16 个组织行、合计行、138 个公式和约 55 种样式。
- `明细` Sheet：55 列、3449 行，前 3 行为元数据和字段表头，数据从第 4 行开始。
- `模版!A3` 引用 `明细!A5`，`模版!E5:L20` 通过 `SUMIFS` 聚合 `明细!W:W`，组织维度使用 `明细!BA:BA`，日期使用 `明细!B:B`，产品分类使用 `明细!C:C`。
- `模版!F5:F20`、`I5:I20` 计算完成率，`J5:J20` 计算排名，`E21:L21` 计算合计。

当前项目的 `WorkflowEngine` 以“所有 Sheet 从第 2 行开始写入映射数据”为默认行为，无法安全覆盖该样例的多行元数据、通报表头和跨 Sheet 明细区域。因此需要新增模板原生模式，并保持现有简单单 Sheet 模式继续可用。

## 1.1 已确认的业务边界

- 模板中的 `模版` 和 `明细` Sheet 是成品的原生 Sheet，生成过程保留二者的名称和结构。
- 每个工作流固定对应一种基础数据结构、一个模板版本和一组明细字段映射。
- 不同基础数据结构通过不同工作流隔离；系统在运行前校验数据源是否满足当前工作流字段契约。
- 组织名称、目标值和通报版式以模板当前内容为准。模板发生变化时，用户上传新模板版本并重新确认工作簿 profile。
- 模板版本之间允许字段集合、Sheet 结构、参数位置和公式范围不同。

## 2. 架构

```mermaid
flowchart LR
    A[上传模板工作簿] --> B[模板结构解析]
    B --> C[Sheet 角色配置]
    C --> D[明细区域配置]
    D --> E[字段映射与参数配置]
    E --> F[公式范围预检]
    F --> G[填充模板明细页]
    G --> H[保留通报页公式与样式]
    H --> I[重算策略与成品校验]
```

### 2.1 模板结构模型

新增 `TemplateWorkbookProfile`，保存：

- Sheet 角色：`notice`、`detail`、`parameter`、`helper`、`ignore`。
- 表头行：支持多行表头和字段名称所在行。
- 数据区域：`data_start_row`、`data_end_row`、列起止范围。
- 公式区域：公式单元格、公式行、公式列、跨 Sheet 引用和风险提示。
- 样式区域：模板数据样式行、通报区域、合计行和新增行复制来源。
- 页面设置：合并范围、冻结窗格、打印区域、打印标题、页眉页脚和隐藏状态。

建议新增配置结构：

```json
{
  "sheets": [
    {"title": "模版", "role": "notice", "data_start_row": null},
    {"title": "明细", "role": "detail", "header_rows": [1, 2, 3], "data_start_row": 4, "data_end_rule": "last_nonempty_row", "style_source_row": 4}
  ],
  "parameters": {
    "report_date": "明细!A5",
    "period_days": "模版!B3"
  },
  "field_contract": {
    "required": ["A", "B", "C", "W", "BA"],
    "workflow_scope": "template_version"
  }
}
```

## 3. 后端组件

### 3.1 `TemplateParser`

在现有 Sheet 和列解析基础上增加：

- 多行非空区域采样。
- 字段行候选识别：包含多个文本字段且下一行包含数据的行。
- 数据起始行识别和人工覆盖。
- Sheet 角色候选：根据 Sheet 名称、公式引用关系和字段密度推荐角色。
- 合并区域完整元数据：范围、左上角单元格、覆盖行列。
- 公式区域分析：公式数量、引用 Sheet、整列引用、固定常量、固定范围和外部引用。
- 页面设置和表格对象解析。

### 3.2 `TemplateNativeEngine`

新增模板原生执行器：

1. 加载模板工作簿。
2. 按 profile 定位明细 Sheet 和数据区域。
3. 清理旧数据区域中的值，保留模板结构和样式。
4. 将数据字段写入明细列，跳过公式列和合并单元格非左上角。
5. 对超出模板数据行的记录复制样式行、行高、隐藏状态和单元格格式。
6. 更新 Excel Table、AutoFilter、打印区域和打印标题的动态范围。
7. 写入参数和通报配置。
8. 保留通报 Sheet 的合并区域、公式、样式和页面设置。
9. 设置 `fullCalcOnLoad`、`forceFullCalc` 和自动计算策略。
10. 输出结构校验结果和公式风险报告。

### 3.3 `FormulaRiskAnalyzer`

新增公式风险分类：

- `fixed_period_constant`：例如 `/31` 或固定月份天数。
- `whole_column_reference`：例如 `W:W`、`BA:BA`。
- `hardcoded_dimension_value`：例如固定产品名称 `升档专用合约`。
- `fixed_rank_range`：例如 `I5:I15`、`I16:I20`。
- `cross_sheet_reference`：跨 Sheet 引用。
- `missing_reference`：引用不存在的 Sheet 或单元格。
- `external_reference`：引用外部工作簿。

样例模板应至少提示：固定 `/31`、整列引用、硬编码产品类型和分段排名范围。提示属于可维护性风险，保留公式原意。

## 4. API 设计

新增接口：

- `POST /api/templates/{template_id}/analyze-workbook`
  - 返回 Sheet 角色候选、数据区域候选、公式统计、样式统计和风险提示。
- `GET /api/templates/{template_id}/workbook-profile`
  - 返回已保存模板配置。
- `PUT /api/templates/{template_id}/workbook-profile`
  - 保存 Sheet 角色、数据区域、字段映射和参数映射。
- `POST /api/templates/{template_id}/workbook-profile/validate`
  - 执行结构、字段、公式引用和范围预检。
- `POST /api/tasks/{task_id}/recalculate`
  - 在支持的 Windows Excel 运行环境中执行重算并保存结果。

现有 `POST /api/tasks/run` 增加执行模式：

```json
{
  "workflow_id": 1,
  "data_source_id": 2,
  "execution_mode": "template_native"
}
```

工作流创建和运行时增加模板版本字段契约校验。数据源字段集合、字段类型和关键字段质量状态需要满足当前工作流 profile；字段结构变化通过新工作流或新模板版本隔离。

## 5. 前端设计

模板中心增加“工作簿分析”流程：

1. Sheet 结构：显示 `模版`、`明细`、可见状态、行列数和公式数。
2. Sheet 角色：选择通报页和明细页。
3. 明细区域：选择字段行、数据起始行、样式来源行和清理策略。
4. 字段映射：展示 55 个字段及类型、样例值和目标列。
5. 公式审查：展示 138 个公式、跨 Sheet 依赖和风险提示。
6. 生成预检：展示数据行数、组织维度覆盖、日期覆盖、产品分类覆盖和公式范围。

生成向导增加“模板结构确认”和“公式重算状态”两个状态信息。

## 6. 正确性约束

1. 明细页的元数据行和字段表头行保持不变。
2. 通报页合并区域保持不变。
3. 明细页数据起始行由 profile 决定，执行器不使用全局固定的第 2 行。
4. 公式列保持公式内容，映射字段不能覆盖模板原生公式。
5. 新增数据行使用模板数据行的样式和行高。
6. 通报页合计行、排名行和参数单元格保持可引用状态。
7. 成品在保存前执行公式引用存在性检查。
8. Linux 环境验证公式文本和结构，Microsoft Excel 负责最终公式计算缓存验证。

## 7. 测试策略

### 单元测试

- 解析样例工作簿的 Sheet 角色和数据区域。
- 解析多行表头和明细字段。
- 复制新增明细行的样式、行高和数字格式。
- 保留合并区域和通报公式。
- 检测固定周期、整列引用、硬编码维度和固定排名范围。

### 集成测试

- 使用样例工作簿和 `明细` 数据生成成品。
- 断言 `模版` 和 `明细` Sheet 均存在。
- 断言 `明细` 的数据从第 4 行开始。
- 断言 `模版!A3`、`模版!E5:L20` 和 `模版!E21:L21` 公式存在。
- 断言合并范围与原模板一致。
- 断言数据超过模板行数时新增行样式一致。

### Windows 验证

- 用 Excel 打开并重算生成文件。
- 检查通报页公式缓存值、排名、完成率、合计和打印预览。
- 检查明细页筛选、冻结、列宽和打印区域。
