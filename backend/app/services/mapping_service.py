import ast
import re
from collections import defaultdict, deque


_FIELD_NAME_RE = re.compile(r"[\s_\-—]+")


def normalize_type(value_type: str | None) -> str:
    value = (value_type or "text").lower()
    if value in {"int", "integer", "float", "number", "decimal"}:
        return "number"
    if value in {"bool", "boolean"}:
        return "bool"
    if value in {"date", "datetime"}:
        return "date"
    if value in {"empty", "none", "null"}:
        return "empty"
    if value == "formula":
        return "formula"
    if value in {"unknown", "mixed"}:
        return value
    return "text"


def normalize_name(value: object) -> str:
    return _FIELD_NAME_RE.sub("", str(value or "")).lower()


def template_columns(template_meta: dict) -> list[dict]:
    result = []
    for sheet in template_meta.get("sheets", []):
        title = sheet.get("title", "")
        for item in sheet.get("columns", []):
            column = str(item.get("column", "")).strip()
            if not title or not column:
                continue
            formula = item.get("formula")
            result.append({
                "target": f"{title}!{column}",
                "sheet": title,
                "column": column,
                "header": item.get("header") or column,
                "type": normalize_type(item.get("type")),
                "is_formula": bool(formula) or item.get("type") == "formula",
                "formula": formula,
                "formula_row": item.get("formula_row"),
                "number_format": item.get("number_format"),
                "formula_references": item.get("formula_references", []),
                "hidden": bool(item.get("hidden", False)),
                "style_signature": item.get("style_signature", ""),
            })
    return result


def data_fields(schema: dict) -> list[dict]:
    fields = []
    for name, meta in schema.items():
        metadata = meta if isinstance(meta, dict) else {"type": str(meta)}
        field_type = normalize_type(metadata.get("type"))
        nullable = bool(metadata.get("nullable", False))
        non_empty_rate = metadata.get("non_empty_rate")
        quality_status = "healthy"
        quality_messages = []
        if field_type == "mixed":
            quality_status = "error"
            quality_messages.append("字段包含混合类型")
        if nullable:
            quality_status = "warning" if quality_status == "healthy" else quality_status
            quality_messages.append("字段存在空值")
        if non_empty_rate is not None and non_empty_rate < 0.8:
            quality_status = "warning" if quality_status == "healthy" else quality_status
            quality_messages.append("字段非空率低于 80%")
        fields.append({"field": name, "type": field_type, "nullable": nullable, "non_empty_rate": non_empty_rate, "sample_values": metadata.get("sample_values", []), "quality_status": quality_status, "quality_messages": quality_messages})
    return fields


def extract_formula_dependencies(expression: str) -> tuple[list[str], str | None]:
    try:
        tree = ast.parse(expression.lstrip("="), mode="eval")
    except SyntaxError as error:
        return [], str(error.msg)
    names = sorted({node.id for node in ast.walk(tree) if isinstance(node, ast.Name)})
    return names, None


def infer_formula_type(expression: str, symbol_types: dict[str, str] | None = None) -> tuple[str, str | None]:
    """Infer the result type of the supported expression subset before execution."""
    symbol_types = symbol_types or {}
    try:
        tree = ast.parse(expression.lstrip("="), mode="eval")
        return _infer_node_type(tree.body, symbol_types), None
    except (SyntaxError, ValueError) as error:
        return "unknown", str(error)


def _infer_node_type(node, symbol_types: dict[str, str]) -> str:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return "bool"
        if isinstance(node.value, (int, float)):
            return "number"
        if isinstance(node.value, str):
            return "text"
        return "unknown"
    if isinstance(node, ast.Name):
        return normalize_type(symbol_types.get(node.id, "unknown"))
    if isinstance(node, ast.BinOp):
        left, right = _infer_node_type(node.left, symbol_types), _infer_node_type(node.right, symbol_types)
        if type(node.op) in {ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow} and left == right == "number":
            return "number"
        if isinstance(node.op, ast.Add) and left == right == "text":
            return "text"
        raise ValueError("四则运算要求依赖字段类型兼容")
    if isinstance(node, ast.Compare):
        return "bool"
    if isinstance(node, ast.BoolOp):
        if all(_infer_node_type(value, symbol_types) == "bool" for value in node.values):
            return "bool"
        raise ValueError("逻辑运算要求布尔字段")
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            return "bool"
        if _infer_node_type(node.operand, symbol_types) == "number":
            return "number"
        raise ValueError("数值负号要求数字字段")
    if isinstance(node, ast.IfExp):
        if _infer_node_type(node.test, symbol_types) != "bool":
            raise ValueError("条件表达式的判断部分必须是布尔类型")
        left, right = _infer_node_type(node.body, symbol_types), _infer_node_type(node.orelse, symbol_types)
        return left if left == right else "unknown"
    raise ValueError(f"不支持的公式节点: {type(node).__name__}")


def type_compatible(source_type: str, target_type: str) -> bool:
    source_type, target_type = normalize_type(source_type), normalize_type(target_type)
    return target_type in {"text", "formula"} or source_type == target_type


def recommend_mapping(columns: list[dict], fields: list[dict]) -> list[dict]:
    recommendations = []
    for column in columns:
        if column["is_formula"]:
            recommendations.append({"target": column["target"], "source_kind": "template_formula", "status": "locked", "candidates": []})
            continue
        candidates = []
        target_name = normalize_name(column["header"])
        for field in fields:
            field_name = normalize_name(field["field"])
            exact = target_name == field_name and bool(target_name)
            contains = bool(target_name and field_name and (target_name in field_name or field_name in target_name))
            type_compatible = type_compatible_for_mapping(field["type"], column["type"])
            score = 1.0 if exact else 0.75 if contains else 0.0
            if score and type_compatible:
                score += 0.1
            if score:
                candidates.append({"field": field["field"], "score": round(min(score, 1.0), 4), "reason": "字段名精确匹配" if exact else "字段名规范化或包含匹配", "type_compatible": type_compatible})
        candidates.sort(key=lambda item: (-item["score"], item["field"]))
        recommendations.append({"target": column["target"], "source_kind": "field", "status": "recommended" if candidates else "unmatched", "candidates": candidates})
    return recommendations


def rules_from_workflow(workflow) -> list[dict]:
    rules = []
    for target, source in (workflow.column_mapping or {}).items():
        rules.append({"target": target, "source_kind": "field", "source_field": source, "expression": None, "dependencies": [source] if source else []})
    nodes = workflow.node_json or {}
    for node in nodes.get("nodes", []):
        config = node.get("data", {}).get("config", node.get("config", {})) or {}
        if node.get("type") == "formula" and config.get("field"):
            dependencies, error = extract_formula_dependencies(config.get("expression", ""))
            rules.append({"target": config["field"], "source_kind": "formula", "source_field": None, "expression": config.get("expression", ""), "dependencies": dependencies, "expression_error": error})
        if node.get("type") == "condition" and config.get("field"):
            rules.append({
                "target": "__condition__",
                "source_kind": "conditional",
                "source_field": config.get("field"),
                "expression": None,
                "dependencies": [config["field"]],
                "operator": config.get("operator", "equals"),
                "value": config.get("value"),
                "node_id": node.get("id"),
            })
        if node.get("type") in {"field_mapping", "write_template"}:
            for target, source in (config.get("mapping") or {}).items():
                rules.append({"target": target, "source_kind": "field", "source_field": source, "expression": None, "dependencies": [source] if source else []})
    return rules


def validate_mapping(columns: list[dict], fields: list[dict], rules: list[dict]) -> dict:
    fields = data_fields({item["field"]: item for item in fields}) if fields and "quality_status" not in fields[0] else fields
    field_types = {item["field"]: item["type"] for item in fields}
    column_by_target = {item["target"]: item for item in columns}
    errors = []
    warnings = []
    seen_targets = defaultdict(int)
    formula_dependencies = {}
    for rule in rules:
        target = rule.get("target", "")
        seen_targets[target] += 1
        column = column_by_target.get(target)
        if column and column["is_formula"] and rule.get("source_kind") != "template_formula":
            errors.append({"target": target, "type": "template_formula_locked", "message": "模板原生公式列不能被基础字段映射覆盖"})
        if rule.get("source_kind") == "field":
            source = rule.get("source_field")
            if source not in field_types:
                errors.append({"target": target, "type": "missing_field", "field": source, "message": f"基础数据字段不存在: {source}"})
            elif column and not type_compatible_for_mapping(field_types[source], column["type"]):
                errors.append({"target": target, "type": "type_conflict", "message": f"字段类型 {field_types[source]} 与目标类型 {column['type']} 不兼容"})
        if rule.get("source_kind") == "formula":
            expression = rule.get("expression", "")
            dependencies, expression_error = extract_formula_dependencies(expression)
            formula_dependencies[target] = dependencies
            if expression_error:
                errors.append({"target": target, "type": "invalid_formula", "message": expression_error})
            for dependency in dependencies:
                if dependency not in field_types and dependency not in {item.get("target") for item in rules}:
                    errors.append({"target": target, "type": "missing_dependency", "field": dependency, "message": f"公式依赖字段不存在: {dependency}"})
            result_type, type_error = infer_formula_type(expression, field_types)
            rule["result_type"] = result_type
            if type_error:
                errors.append({"target": target, "type": "formula_type_error", "message": type_error})
            elif column and not type_compatible_for_mapping(result_type, column["type"]):
                errors.append({"target": target, "type": "formula_type_conflict", "message": f"公式结果类型 {result_type} 与目标类型 {column['type']} 不兼容"})
    for target, count in seen_targets.items():
        if count > 1:
            errors.append({"target": target, "type": "duplicate_target", "message": f"模板输出列存在 {count} 条映射规则"})
    required_targets = {item["target"] for item in columns if not item["is_formula"]}
    mapped_targets = set(seen_targets)
    for target in sorted(required_targets - mapped_targets):
        errors.append({"target": target, "type": "unmapped_target", "message": "必需模板输出列尚未配置映射"})
    dependency_order, cycle = _dependency_order(formula_dependencies)
    if cycle:
        errors.append({"target": cycle[0], "type": "circular_dependency", "message": f"公式存在循环依赖: {' -> '.join(cycle)}"})
    if not errors and any(item["status"] == "recommended" for item in recommend_mapping(columns, fields)):
        warnings.append({"type": "recommendation_pending", "message": "存在自动推荐映射，生成前需要人工确认"})
    return {"valid": not errors, "errors": errors, "warnings": warnings, "dependency_order": dependency_order, "mapped_count": len(mapped_targets), "required_count": len(required_targets), "error_count": len(errors), "warning_count": len(warnings), "field_quality": {item["field"]: {"status": item.get("quality_status", "healthy"), "messages": item.get("quality_messages", [])} for item in fields}}


def type_compatible_for_mapping(source_type: str, target_type: str) -> bool:
    return type_compatible(source_type, target_type)


def _dependency_order(dependencies: dict[str, list[str]]) -> tuple[list[str], list[str] | None]:
    nodes = set(dependencies)
    indegree = {node: 0 for node in nodes}
    adjacency = defaultdict(set)
    for target, values in dependencies.items():
        for dependency in values:
            if dependency in nodes:
                adjacency[dependency].add(target)
                indegree[target] += 1
    queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for target in sorted(adjacency[node]):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if len(order) == len(nodes):
        return order, None
    remaining = sorted(nodes - set(order))
    return order, remaining + ([remaining[0]] if remaining else [])
