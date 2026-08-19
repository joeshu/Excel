from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


SUPPORTED_AGGREGATES = {"sum", "count", "count_distinct", "avg", "max"}
SUPPORTED_OPERATORS = {"equals", "not_equals", "in", "contains", "gt", "gte", "lt", "lte"}


def calculate_notice(records: list[dict], config: dict) -> dict:
    """Calculate a configurable notice matrix without depending on a workbook layout."""
    dimensions = config.get("dimensions") or {}
    source_dimension = dimensions.get("source_field")
    rule_field = dimensions.get("rule_field")
    rule_value = dimensions.get("rule_value")
    rows = config.get("rows") or []
    metrics = config.get("metrics") or {}
    selected = [record for record in records if _matches_rule(record, rule_field, rule_value)]
    normalized_rows = [_normalize_record(record) for record in selected]
    contexts = [_row_context(row, source_dimension, rows) for row in rows]
    values: dict[str, dict[str, Any]] = {str(item["row"]): {} for item in rows}
    traces: list[dict] = []

    for metric_name, metric in metrics.items():
        if metric.get("kind") in {"derived", "ratio", "rank"}:
            continue
        for context in contexts:
            matching = [record for record in normalized_rows if _matches_metric(record, context, metric)]
            value = _aggregate(matching, metric)
            values[str(context["row"])][metric_name] = value
            traces.append({"row": context["row"], "metric": metric_name, "matched_rows": len(matching), "value": value})

    for metric_name, metric in metrics.items():
        if metric.get("kind") not in {"ratio", "derived"}:
            continue
        numerator = metric.get("numerator") or metric.get("source_metric") or "daily"
        denominator = metric.get("denominator") or "target"
        for context in contexts:
            row_values = values[str(context["row"])]
            top = _to_number(row_values.get(numerator))
            bottom = _to_number(row_values.get(denominator))
            if denominator == "target":
                bottom = _to_number(context.get("target"))
            ratio = _ratio(top, bottom, metric.get("zero_policy", "zero"))
            if metric.get("kind") == "derived" and metric.get("formula") == "progressive_rate":
                elapsed_days = _to_number(metric.get("elapsed_days")) or 0
                total_days = _to_number(metric.get("total_days")) or 0
                elapsed_days = elapsed_days or _to_number(context.get(metric.get("elapsed_days_ref"))) or 0
                ratio = _clean_number(_ratio(top, bottom, metric.get("zero_policy", "zero")) * total_days / elapsed_days) if elapsed_days and total_days else 0
                row_values[metric_name] = ratio

    for metric_name, metric in metrics.items():
        if metric.get("kind") != "rank":
            continue
        source_metric = metric.get("source_metric")
        ordered = sorted(contexts, key=lambda item: _to_number(values[str(item["row"])].get(source_metric)) or 0, reverse=metric.get("direction", "desc") == "desc")
        rank = 0
        previous = object()
        for index, context in enumerate(ordered, start=1):
            current = _to_number(values[str(context["row"])].get(source_metric)) or 0
            if metric.get("tie", "competition") == "competition" and current != previous:
                rank = index
            elif metric.get("tie", "competition") == "dense" and current != previous:
                rank += 1
            else:
                rank = index if metric.get("tie", "competition") == "ordinal" else rank
            values[str(context["row"])][metric_name] = rank
            previous = current

    totals = _calculate_totals(values, rows, metrics, config.get("totals") or {})
    return {"values": values, "totals": totals, "traces": traces, "matched_rows": len(normalized_rows)}


def _normalize_record(record: dict) -> dict:
    return {str(key).strip(): value for key, value in record.items()}


def _row_context(record: dict, source_field: str | None, rows: list[dict]) -> dict:
    return dict(record)


def _matches_rule(record: dict, field: str | None, value: Any) -> bool:
    return not field or value in {None, ""} or record.get(field) == value


def _matches_metric(record: dict, context: dict, metric: dict) -> bool:
    dimension_field = metric.get("dimension_field")
    dimension_value = context.get("key")
    if dimension_field and record.get(dimension_field) != dimension_value:
        aliases = context.get("aliases") or []
        if record.get(dimension_field) not in aliases:
            return False
    if not _matches_date(record, metric):
        return False
    return all(_matches_filter(record, item) for item in metric.get("filters") or [])


def _matches_date(record: dict, metric: dict) -> bool:
    date_config = metric.get("date") or {}
    field = date_config.get("field")
    expected = date_config.get("value")
    if not field or expected in {None, ""}:
        return True
    actual = _date_key(record.get(field), date_config.get("scope", "day"))
    return actual == _date_key(expected, date_config.get("scope", "day"))


def _date_key(value: Any, scope: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip().replace("-", "")
    if isinstance(value, (datetime, date)):
        text = value.strftime("%Y%m%d")
    digits = "".join(char for char in text if char.isdigit())
    if len(digits) < 6:
        return text
    return digits[:6] if scope == "month" else digits[:8]


def _matches_filter(record: dict, condition: dict) -> bool:
    field = condition.get("field")
    operator = condition.get("operator", "equals")
    if operator not in SUPPORTED_OPERATORS:
        raise ValueError(f"不支持的筛选操作符: {operator}")
    actual = record.get(field)
    expected = condition.get("value")
    if operator == "equals":
        return actual == expected
    if operator == "not_equals":
        return actual != expected
    if operator == "in":
        return actual in (expected or [])
    if operator == "contains":
        return str(expected) in str(actual or "")
    left, right = _to_number(actual), _to_number(expected)
    if left is None or right is None:
        return False
    return {"gt": left > right, "gte": left >= right, "lt": left < right, "lte": left <= right}[operator]


def _aggregate(records: list[dict], metric: dict) -> int | float | None:
    aggregate = metric.get("aggregate", "sum")
    if aggregate not in SUPPORTED_AGGREGATES:
        raise ValueError(f"不支持的聚合方式: {aggregate}")
    field = metric.get("source_field")
    if aggregate == "count":
        return len(records)
    if aggregate == "count_distinct":
        return len({record.get(field) for record in records if record.get(field) not in {None, ""}})
    numbers = [_to_number(record.get(field)) for record in records]
    numbers = [item for item in numbers if item is not None]
    if not numbers:
        return metric.get("empty_policy", "zero") == "null" and None or 0
    if aggregate == "sum":
        return _clean_number(sum(numbers))
    if aggregate == "avg":
        return _clean_number(sum(numbers) / len(numbers))
    return _clean_number(max(numbers))


def _calculate_totals(values: dict[str, dict], rows: list[dict], metrics: dict, totals: dict) -> dict:
    result = {}
    for metric_name, metric in metrics.items():
        if metric.get("kind") == "rank":
            result[metric_name] = None
            continue
        operation = (totals.get(metric_name) or {}).get("operation", "sum")
        items = [_to_number(value.get(metric_name)) for value in values.values()]
        items = [item for item in items if item is not None]
        if operation == "avg" and items:
            result[metric_name] = _clean_number(sum(items) / len(items))
        elif operation == "max" and items:
            result[metric_name] = _clean_number(max(items))
        elif metric.get("kind") == "ratio":
            numerator_name = metric.get("numerator") or metric.get("source_metric")
            denominator_name = metric.get("denominator")
            numerator = sum(_to_number(value.get(numerator_name)) or 0 for value in values.values())
            denominator = sum(_to_number(value.get(denominator_name)) or 0 for value in values.values()) if denominator_name else sum(_to_number(row.get("target")) or 0 for row in rows)
            result[metric_name] = _ratio(numerator, denominator, metric.get("zero_policy", "zero"))
        elif metric.get("kind") == "derived" and metric.get("source_metric"):
            numerator = sum(_to_number(value.get(metric["source_metric"])) or 0 for value in values.values())
            denominator = sum(_to_number(row.get("target")) or 0 for row in rows)
            result[metric_name] = _ratio(numerator, denominator, metric.get("zero_policy", "zero"))
        else:
            result[metric_name] = _clean_number(sum(items)) if items else 0
    return result


def _ratio(numerator: float | None, denominator: float | None, zero_policy: str) -> int | float | None:
    if not denominator:
        return None if zero_policy == "null" else 0
    return _clean_number((numerator or 0) / denominator)


def _to_number(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(Decimal(str(value).replace(",", "")))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _clean_number(value: float) -> int | float:
    return int(value) if value.is_integer() else round(value, 6)
