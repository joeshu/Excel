from __future__ import annotations

from dataclasses import dataclass

from app.services.dag_engine import referenced_fields
from app.services.template_contract import native_required_fields


@dataclass
class WorkflowMatch:
    workflow_id: int
    score: float
    matched_fields: list[str]
    missing_fields: list[str]
    reasons: list[str]


def match_workflows(data_source, workflows, templates) -> list[dict]:
    source_fields = set(data_source.schema_ or {})
    results = []
    template_by_id = {template.id: template for template in templates}
    for workflow in workflows:
        template = template_by_id.get(workflow.template_id)
        required = set()
        if workflow.mode == "dag":
            required = referenced_fields(workflow.node_json or {})
        elif workflow.mode == "template_native":
            profile = (template.column_meta or {}).get("native_profile", {}) if template else {}
            required = set(native_required_fields(profile, workflow.column_mapping))
        else:
            required = {field for field in (workflow.column_mapping or {}).values() if field}
        matched = sorted(required & source_fields)
        missing = sorted(required - source_fields)
        score = 1.0 if not required else len(matched) / len(required)
        reasons = [f"匹配 {len(matched)} 个字段"]
        if template:
            reasons.append(f"模板版本 {template.version}")
        if not missing:
            reasons.append("数据源满足工作流字段要求")
        else:
            reasons.append(f"缺少 {len(missing)} 个字段")
        results.append({"workflow_id": workflow.id, "workflow_name": workflow.name, "mode": workflow.mode, "template_id": workflow.template_id, "score": round(score, 4), "matched_fields": matched, "missing_fields": missing, "reasons": reasons})
    return sorted(results, key=lambda item: (-item["score"], item["workflow_id"]))
