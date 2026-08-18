from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.data_source import DataSource
from app.models.template import Template
from app.models.workflow import WorkflowDef
from app.services.data_reader import read_records
from app.services.dag_engine import validate_dag
from app.services.template_parser import TemplateParser


def example_root() -> Path:
    if getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS) / "sample_data" / "scenarios"
    return Path(__file__).resolve().parents[3] / "sample_data" / "scenarios"


def seed_examples(db: Session) -> None:
    root = example_root()
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    target_dir = Path(settings.upload_dir) / "examples"
    target_dir.mkdir(parents=True, exist_ok=True)
    templates: dict[str, Template] = {}
    sources: dict[str, DataSource] = {}
    for scenario in manifest["scenarios"]:
        name = scenario["name"]
        source_file = root / scenario["source"]["path"]
        template_file = root / scenario["template"]
        if not source_file.is_file() or not template_file.is_file():
            continue
        source = db.scalar(select(DataSource).where(DataSource.is_example.is_(True), DataSource.name == f"示例数据：{name}"))
        source_target = target_dir / source_file.name
        if not source_target.is_file():
            shutil.copy2(source_file, source_target)
        records = read_records(str(source_target))
        schema = {field: {"required": False, "type": type(value).__name__} for field, value in (records[0].items() if records else [])}
        if source is None:
            source = DataSource(name=f"示例数据：{name}", source_type="example", schema_=schema, file_path=str(source_target), is_example=True)
            db.add(source)
            db.flush()
        else:
            source.file_path = str(source_target)
            source.schema_ = schema
        template = db.scalar(select(Template).where(Template.is_example.is_(True), Template.name == f"示例模板：{name}"))
        template_target = target_dir / template_file.name
        if not template_target.is_file():
            shutil.copy2(template_file, template_target)
        metadata = TemplateParser().parse(str(template_target))
        if template is None:
            template = Template(name=f"示例模板：{name}", file_path=str(template_target), has_formula=metadata["has_formula"], column_meta=metadata, sheet_count=metadata["sheet_count"], version="example", is_example=True)
            db.add(template)
            db.flush()
        else:
            template.file_path = str(template_target)
            template.column_meta = metadata
            template.has_formula = metadata["has_formula"]
            template.sheet_count = metadata["sheet_count"]
        templates[name] = template
        sources[name] = source
        mapping = scenario.get("mapping", {})
        workflow_name = f"示例工作流：{name}（模式 A）"
        if db.scalar(select(WorkflowDef).where(WorkflowDef.is_example.is_(True), WorkflowDef.name == workflow_name)) is None:
            db.add(WorkflowDef(template_id=template.id, name=workflow_name, mode="formula", column_mapping=mapping, is_example=True))
    db.flush()
    basic = templates.get("basic_no_formula")
    basic_source = sources.get("basic_no_formula")
    if basic and basic_source:
        dag_name = "示例工作流：basic_no_formula（模式 B）"
        if db.scalar(select(WorkflowDef).where(WorkflowDef.is_example.is_(True), WorkflowDef.name == dag_name)) is None:
            nodes = [
                {"id": "source", "type": "data_source", "data": {"config": {"source_id": basic_source.id}, "label": "data_source"}},
                {"id": "mapping", "type": "field_mapping", "data": {"config": {"mapping": {"数据模板!A": "customer_id", "数据模板!B": "customer_name", "数据模板!C": "region", "数据模板!D": "level", "数据模板!E": "signup_date", "数据模板!F": "active"}}, "label": "field_mapping"}},
                {"id": "write", "type": "write_template", "data": {"config": {"mapping": {"数据模板!A": "customer_id", "数据模板!B": "customer_name", "数据模板!C": "region", "数据模板!D": "level", "数据模板!E": "signup_date", "数据模板!F": "active"}}, "label": "write_template"}},
                {"id": "output", "type": "output_file", "data": {"label": "output_file"}},
            ]
            edges = [{"source": "source", "target": "mapping"}, {"source": "mapping", "target": "write"}, {"source": "write", "target": "output"}]
            node_json = {"nodes": nodes, "edges": edges}
            if validate_dag(node_json)["valid"]:
                db.add(WorkflowDef(template_id=basic.id, name=dag_name, mode="dag", node_json=node_json, is_example=True))
    complex_template = templates.get("multi_sheet_complex")
    complex_source = sources.get("multi_sheet_complex")
    if complex_template and complex_source:
        dag_name = "示例工作流：multi_sheet_complex（模式 B）"
        if db.scalar(select(WorkflowDef).where(WorkflowDef.is_example.is_(True), WorkflowDef.name == dag_name)) is None:
            mapping = {
                "数据模板!A": "record_id", "数据模板!B": "order_no", "数据模板!C": "region",
                "数据模板!D": "category", "数据模板!E": "quantity", "数据模板!F": "unit_price",
                "数据模板!G": "discount_rate", "数据模板!H": "owner", "数据模板!J": "status",
            }
            nodes = [
                {"id": "source", "type": "data_source", "data": {"config": {"source_id": complex_source.id}, "label": "data_source"}},
                {"id": "mapping", "type": "field_mapping", "data": {"config": {"mapping": mapping}, "label": "field_mapping"}},
                {"id": "formula", "type": "formula", "data": {"config": {"field": "amount", "expression": "quantity * unit_price"}, "label": "formula"}},
                {"id": "condition", "type": "condition", "data": {"config": {"field": "quantity", "operator": "greater_than", "value": 0}, "label": "condition"}},
                {"id": "write", "type": "write_template", "data": {"config": {"mapping": mapping}, "label": "write_template"}},
                {"id": "output", "type": "output_file", "data": {"label": "output_file"}},
            ]
            edges = [{"source": "source", "target": "mapping"}, {"source": "mapping", "target": "formula"}, {"source": "formula", "target": "condition"}, {"source": "condition", "target": "write"}, {"source": "write", "target": "output"}]
            node_json = {"nodes": nodes, "edges": edges}
            if validate_dag(node_json)["valid"]:
                db.add(WorkflowDef(template_id=complex_template.id, name=dag_name, mode="dag", node_json=node_json, is_example=True))
    db.commit()
