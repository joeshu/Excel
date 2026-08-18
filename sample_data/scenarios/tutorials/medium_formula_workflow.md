# 中等教程：订单金额公式工作流

## 适合学习什么

这个示例使用模式 A，练习单 Sheet 字段映射、行级公式、质量检查和公式结果预览。示例对象名称如下：

- 模板：`示例模板：standard_formula`
- 数据源：`示例数据：standard_formula`
- 工作流：`示例工作流：standard_formula（模式 A）`

## 操作步骤

1. 打开模板中心，找到 `standard_formula`，点击“预览”查看字段和公式列。
2. 点击“公式检查”，确认模板包含 90 个公式，公式列为 `gross_amount`、`net_amount` 和 `risk`。
3. 打开工作流中心，找到对应的模式 A 示例，点击“查看映射”。
4. 对照以下映射检查配置：

| 模板列 | 数据源字段 |
| --- | --- |
| `数据模板!A` | `order_id` |
| `数据模板!B` | `region` |
| `数据模板!C` | `category` |
| `数据模板!D` | `quantity` |
| `数据模板!E` | `unit_price` |
| `数据模板!F` | `discount_rate` |

5. 进入任务执行，选择 `示例数据：standard_formula`，点击“数据质量检查”。
6. 返回工作流并生成 Excel，等待任务状态变成 `success`。
7. 在任务历史中点击“公式结果”，检查缓存值和错误状态。

## 关键公式

```text
gross_amount = quantity * unit_price
net_amount = gross_amount * (1 - discount_rate)
risk = IF(net_amount > 2000, "复核", "正常")
```

## 预期结果

- 输出文件保留模板样式和公式。
- 输出文件包含 30 条订单数据。
- 每条数据生成金额和风险结果。
- 当前环境没有 Excel 或 LibreOffice 时，任务计算引擎显示 `formula_only`，文件仍可由 Excel 打开重算。

## 常见问题

- 映射保存失败：检查每个非公式模板列是否都有数据源字段。
- 金额为空：检查数据源字段名称是否与映射完全一致。
- 公式值显示“未缓存”：使用 Windows Excel 或 LibreOffice 打开一次文件完成计算。
