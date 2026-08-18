# 复杂教程：多 Sheet 订单审核 DAG

## 适合学习什么

这个示例以多 Sheet 订单模板为基础，演示模式 B 的数据源节点、字段映射节点、公式节点、条件节点、写入模板节点和输出节点。示例对象名称如下：

- 模板：`示例模板：multi_sheet_complex`
- 数据源：`示例数据：multi_sheet_complex`
- 推荐参考工作流：`示例工作流：multi_sheet_complex（模式 B）`

工作流中心已经内置该模式 B 示例，可以直接点击“查看流程”；也可以复制后再调整节点。

## 操作步骤

1. 打开模板中心，找到 `multi_sheet_complex`，点击“预览”。
2. 查看 `数据模板`、`区域字典` 和 `汇总` 三个 Sheet。
3. 点击“配置模式 B”，依次添加以下节点：

| 节点类型 | 关键配置 |
| --- | --- |
| `data_source` | 选择 `示例数据：multi_sheet_complex` |
| `field_mapping` | 将输入字段映射到 `数据模板` 的 A-H、J 列 |
| `formula` | 输出字段 `amount`，表达式 `quantity * unit_price * (1 - discount_rate)` |
| `condition` | 字段 `quantity`，操作 `greater_than`，比较值 `0` |
| `write_template` | 写入 `数据模板!A` 至 `数据模板!J` |
| `output_file` | 保持默认配置 |

4. 按顺序连线：

```text
data_source -> field_mapping -> formula -> condition -> write_template -> output_file
```

5. 保存流程。保存时系统会根据模板表头和数据源字段自动提示映射。
6. 点击“运行流程”，确认任务使用的数据源和节点配置一致。
7. 任务完成后，在任务历史下载文件，并查看公式结果预览。

## 推荐字段映射

| 模板列 | 数据源字段 |
| --- | --- |
| `数据模板!A` | `record_id` |
| `数据模板!B` | `order_no` |
| `数据模板!C` | `region` |
| `数据模板!D` | `category` |
| `数据模板!E` | `quantity` |
| `数据模板!F` | `unit_price` |
| `数据模板!G` | `discount_rate` |
| `数据模板!H` | `owner` |
| `数据模板!J` | `status` |

## 复杂点说明

- `数据模板!I` 使用公式生成金额，`汇总` Sheet 使用 `SUMIF` 汇总区域金额。
- `区域字典` Sheet 为查找公式提供区域等级数据。
- 条件节点会过滤掉 `quantity <= 0` 的记录。
- 数据源包含缺失折扣率和零数量，用于观察质量报告与条件过滤效果。
- DAG 保存和运行前会检查节点类型、循环依赖、不可达节点和输出节点连通性。

## 排错顺序

1. 检查数据源节点是否选择了正确的数据源。
2. 检查所有非公式模板列是否完成映射。
3. 检查公式表达式中的字段名称是否存在于数据源字段。
4. 检查输出节点是否连接到写入模板节点。
5. 先执行数据质量检查，再运行流程。
