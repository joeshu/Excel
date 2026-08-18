# 场景样例

运行 `PYTHONPATH=backend python3 tools/generate_scenario_samples.py` 可按固定随机种子重新生成全部场景。

| 场景 | 数据规模 | 模板特征 | 覆盖内容 |
| --- | ---: | --- | --- |
| `basic_no_formula` | 12 行、6 字段 | 无公式、客户主数据 | 模式 A 无公式全流程、模式 B DAG 无公式全流程 |
| `standard_formula` | 30 行、9 字段 | 3 列行级公式 | 简单乘法、折扣、风险判断 |
| `multi_sheet_complex` | 120 行、10 字段 | 3 Sheet、128 个公式 | `SUMIF`、`VLOOKUP`、跨 Sheet 汇总、缺失值和零值 |
| `quality_edge_cases` | 40 行、6 字段 | 无公式、异常数据 | 空值、混合类型、CSV/XLSX 双格式 |

场景清单、字段映射和公式数量记录在 `manifest.json`。对应回归测试位于 `backend/tests/test_scenario_samples.py`。
