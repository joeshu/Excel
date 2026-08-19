from __future__ import annotations

from openpyxl.utils import get_column_letter


def emit_notice_formulas(config: dict, detail_sheet: str = "明细") -> dict[str, dict[str, str]]:
    """Emit auditable Excel formulas for the configured notice matrix."""
    dimensions = config.get("dimensions") or {}
    source_dimension = dimensions.get("source_column") or dimensions.get("source_field", "BA")
    rule_field = dimensions.get("rule_field")
    rule_value = dimensions.get("rule_value")
    date_field = dimensions.get("date_column") or dimensions.get("date_field", "A")
    date_cell = dimensions.get("date_cell", "'模版'!$A$3")
    metrics = config.get("metrics") or {}
    formulas: dict[str, dict[str, str]] = {}
    for row in config.get("rows") or []:
        row_number = int(row["row"])
        formulas[str(row_number)] = {}
        criteria = [f"{_sheet_ref(detail_sheet)}!${source_dimension}:${source_dimension}", f'$B{row_number}']
        if rule_field and rule_value not in {None, ""}:
            criteria.extend([f"{_sheet_ref(detail_sheet)}!${rule_field}:${rule_field}", _quote(rule_value)])
        for name, metric in metrics.items():
            column = metric.get("column")
            if not column:
                continue
            kind = metric.get("kind", "aggregate")
            if kind in {"derived", "ratio"}:
                continue
            source_field = metric.get("source_column") or metric.get("source_field")
            if metric.get("aggregate", "sum") == "count":
                formula = f'=COUNTIFS({", ".join(criteria)})'
            elif metric.get("aggregate") == "count_distinct":
                formula = f'=SUMPRODUCT(({_sheet_ref(detail_sheet)}!${source_dimension}:${source_dimension}=$B{row_number})*({_sheet_ref(detail_sheet)}!${source_field}:${source_field}<>""))'
            else:
                formula = f'=SUMIFS({_sheet_ref(detail_sheet)}!${source_field}:${source_field},{", ".join(criteria)})'
            for condition in metric.get("filters") or []:
                condition_column = condition.get("column") or condition.get("field")
                if condition_column and condition.get("operator", "equals") == "equals":
                    formula = formula[:-1] + f', {_sheet_ref(detail_sheet)}!${condition_column}:${condition_column}, {_quote(condition.get("value"))})'
            if metric.get("date", {}).get("column") or metric.get("date", {}).get("field"):
                date_column = metric["date"].get("column") or metric["date"]["field"]
                formula = formula[:-1] + f', {_sheet_ref(detail_sheet)}!${date_column}:${date_column}, {date_cell})'
            formulas[str(row_number)][name] = formula
        for name, metric in metrics.items():
            column = metric.get("column")
            if not column:
                continue
            if metric.get("kind") in {"derived", "ratio"}:
                source = metric.get("source_metric") or metric.get("numerator") or "daily"
                source_column = metrics.get(source, {}).get("column")
                denominator = metric.get("denominator")
                if metric.get("formula") == "progressive_rate":
                    total_days = metric.get("total_days") or 31
                    elapsed_ref = metric.get("elapsed_days_ref") or "B3"
                    formula = f'=IFERROR({source_column}{row_number}/D{row_number}*{total_days}/{elapsed_ref},0)'
                elif denominator == "target" or not denominator:
                    formula = f'=IFERROR({source_column}{row_number}/D{row_number},0)'
                else:
                    denominator_column = metrics.get(denominator, {}).get("column")
                    formula = f'=IFERROR({source_column}{row_number}/{denominator_column}{row_number},0)'
                formulas[str(row_number)][name] = formula
            elif metric.get("kind") == "rank":
                source = metric.get("source_metric", "daily")
                source_column = metrics.get(source, {}).get("column", "E")
                first = min(int(item["row"]) for item in config.get("rows") or [row])
                last = max(int(item["row"]) for item in config.get("rows") or [row])
                formulas[str(row_number)][name] = f'=RANK({source_column}{row_number},${source_column}${first}:${source_column}${last},0)'
    return formulas


def _quote(value: object) -> str:
    return '"' + str(value).replace('"', '""') + '"'


def _sheet_ref(name: str) -> str:
    escaped = str(name).replace("'", "''")
    return escaped if escaped.replace("_", "").isalnum() else f"'{escaped}'"
