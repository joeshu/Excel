import ast
import operator
from collections import defaultdict, deque
from copy import deepcopy

from app.services.workflow_engine import WorkflowEngine

NODE_TYPES = {"data_source", "field_mapping", "formula", "condition", "write_template", "output_file"}
_OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def validate_dag(node_json: dict) -> dict:
    nodes = node_json.get("nodes", [])
    edges = node_json.get("edges", [])
    node_ids = [node.get("id") for node in nodes]
    issues = []
    if len(node_ids) != len(set(node_ids)):
        issues.append("节点 ID 必须唯一")
    known_ids = set(node_ids)
    if not nodes:
        issues.append("流程至少需要一个节点")
    for node in nodes:
        if node.get("type") not in NODE_TYPES:
            issues.append(f"不支持的节点类型: {node.get('type')}")
    node_types = {node.get("type") for node in nodes}
    for required_type in ("data_source", "write_template", "output_file"):
        if required_type not in node_types:
            issues.append(f"流程缺少 {required_type} 节点")
    adjacency = defaultdict(list)
    indegree = {node_id: 0 for node_id in known_ids}
    for edge in edges:
        source, target = edge.get("source"), edge.get("target")
        if source not in known_ids or target not in known_ids:
            issues.append(f"边引用了不存在的节点: {source} -> {target}")
            continue
        adjacency[source].append(target)
        indegree[target] += 1
    original_indegree = indegree.copy()
    queue = deque(node_id for node_id, degree in indegree.items() if degree == 0)
    ordered = []
    while queue:
        node_id = queue.popleft()
        ordered.append(node_id)
        for target in adjacency[node_id]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if len(ordered) != len(known_ids):
        issues.append("流程包含循环依赖")
    roots = {node_id for node_id, degree in original_indegree.items() if degree == 0}
    if known_ids:
        reachable = set(roots)
        pending = deque(roots)
        while pending:
            source = pending.popleft()
            for target in adjacency[source]:
                if target not in reachable:
                    reachable.add(target)
                    pending.append(target)
        if len(reachable) != len(known_ids):
            issues.append("流程存在不可达节点")
    output_ids = {node.get("id") for node in nodes if node.get("type") == "output_file"}
    if output_ids and not any(output_id in adjacency[source] for source in adjacency for output_id in output_ids):
        issues.append("输出文件节点必须接收上游节点")
    return {"valid": not issues, "issues": issues, "order": ordered}


def execute_dag(node_json: dict, records: list[dict], template_path: str, output_path: str) -> str:
    validation = validate_dag(node_json)
    if not validation["valid"]:
        raise ValueError("；".join(validation["issues"]))
    nodes = {node["id"]: node for node in node_json["nodes"]}
    current_records = deepcopy(records)
    column_mapping = {}
    for node_id in validation["order"]:
        node = nodes[node_id]
        config = node.get("data", {}).get("config", node.get("config", {})) or {}
        node_type = node["type"]
        if node_type == "data_source":
            continue
        if node_type == "field_mapping":
            column_mapping.update(config.get("mapping", {}))
        elif node_type == "formula":
            field = config.get("field")
            expression = config.get("expression", "")
            if not field or not expression:
                raise ValueError("公式计算节点需要 field 和 expression")
            for record in current_records:
                record[field] = _evaluate_expression(expression, record)
        elif node_type == "condition":
            field, expected, comparison = config.get("field"), config.get("value"), config.get("operator", "equals")
            if not field:
                raise ValueError("条件判断节点需要 field")
            current_records = [record for record in current_records if _matches(record.get(field), comparison, expected)]
        elif node_type == "write_template":
            column_mapping.update(config.get("mapping", {}))
        elif node_type == "output_file":
            continue
    if not column_mapping:
        raise ValueError("写入模板节点至少需要一个字段映射")
    engine = WorkflowEngine(template_path)
    engine.execute_formula_mode(current_records, column_mapping)
    engine.save(output_path)
    return output_path


def referenced_fields(node_json: dict) -> set[str]:
    fields = set()
    for node in node_json.get("nodes", []):
        config = node.get("data", {}).get("config", node.get("config", {})) or {}
        fields.update(value for value in (config.get("mapping") or {}).values() if value)
        if node.get("type") in {"formula", "condition"} and config.get("expression"):
            fields.update(name.id for name in ast.walk(ast.parse(config["expression"], mode="eval")) if isinstance(name, ast.Name))
        if node.get("type") == "condition" and config.get("field"):
            fields.add(config["field"])
    return fields


def _evaluate_expression(expression: str, record: dict):
    tree = ast.parse(expression, mode="eval")
    return _evaluate_node(tree.body, record)


def _evaluate_node(node, record):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, str)):
        return node.value
    if isinstance(node, ast.Name):
        return _coerce_number(record.get(node.id, 0))
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        left, right = _evaluate_node(node.left, record), _evaluate_node(node.right, record)
        if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
            raise ValueError("公式字段必须是数字，无法执行四则运算")
        return _OPERATORS[type(node.op)](left, right)
    raise ValueError("公式表达式仅支持字段、数字、字符串和四则运算")


def _coerce_number(value):
    if isinstance(value, str):
        stripped = value.strip()
        try:
            return float(stripped) if "." in stripped else int(stripped)
        except ValueError:
            return value
    return value


def _matches(actual, comparison: str, expected) -> bool:
    if comparison == "equals":
        return actual == expected
    if comparison == "not_equals":
        return actual != expected
    if comparison in {"greater_than", "less_than"}:
        try:
            return actual > expected if comparison == "greater_than" else actual < expected
        except TypeError:
            return False
    raise ValueError(f"不支持的条件操作符: {comparison}")
