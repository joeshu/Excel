from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.template import Template
from app.models.data_source import DataSource
from app.models.workflow import WorkflowDef
from app.schemas.workflow import DagUpdate, MappingUpdate, WorkflowCreate, WorkflowWizardCreate
from app.services.dag_engine import validate_dag
from app.services.domain_metadata import field_signature

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.post("", status_code=201)
def create_workflow(payload: WorkflowCreate, db: Session = Depends(get_db)):
    if not db.get(Template, payload.template_id):
        raise HTTPException(status_code=404, detail="模板不存在")
    workflow = WorkflowDef(template_id=payload.template_id, name=payload.name, mode=payload.mode)
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow


@router.post("/wizard", status_code=201)
def create_workflow_from_wizard(payload: WorkflowWizardCreate, db: Session = Depends(get_db)):
    source = db.get(DataSource, payload.data_source_id)
    template = db.get(Template, payload.template_id)
    if not source or not template:
        raise HTTPException(status_code=404, detail="数据源或模板不存在")
    workflow = WorkflowDef(template_id=payload.template_id, name=payload.name, mode=payload.mode, column_mapping=payload.column_mapping, node_json=payload.node_json, applicable_field_signature=source.field_signature)
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow


@router.get("")
def list_workflows(db: Session = Depends(get_db)):
    return db.scalars(select(WorkflowDef).order_by(WorkflowDef.updated_at.desc())).all()


@router.put("/{workflow_id}/mapping")
def update_mapping(workflow_id: int, payload: MappingUpdate, db: Session = Depends(get_db)):
    workflow = db.get(WorkflowDef, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    if workflow.mode != "formula":
        raise HTTPException(status_code=400, detail="只有模式 A 支持列映射")
    template = db.get(Template, workflow.template_id)
    sheets = template.column_meta.get("sheets", [])
    first_sheet = sheets[0]["title"] if sheets else ""
    normalized_mapping = {
        key if "!" in key else f"{first_sheet}!{key}": value
        for key, value in payload.column_mapping.items()
    }
    valid_columns = {
        f"{sheet['title']}!{item['column']}"
        for sheet in template.column_meta.get("sheets", [])
        for item in sheet.get("columns", [])
        if item.get("type") != "formula"
    }
    invalid_columns = sorted(set(normalized_mapping) - valid_columns)
    empty_fields = sorted(column for column in valid_columns if not normalized_mapping.get(column, "").strip())
    if invalid_columns:
        raise HTTPException(status_code=400, detail=f"存在不可映射的模板列: {', '.join(invalid_columns)}")
    if empty_fields:
        raise HTTPException(status_code=400, detail=f"以下模板列尚未配置数据源字段: {', '.join(empty_fields)}")
    workflow.column_mapping = normalized_mapping
    workflow.applicable_field_signature = field_signature(normalized_mapping.values())
    db.commit()
    db.refresh(workflow)
    return workflow


@router.post("/{workflow_id}/copy", status_code=201)
def copy_workflow(workflow_id: int, db: Session = Depends(get_db)):
    source = db.get(WorkflowDef, workflow_id)
    if not source:
        raise HTTPException(status_code=404, detail="工作流不存在")
    copied = WorkflowDef(template_id=source.template_id, name=f"{source.name} 副本", mode=source.mode, node_json=source.node_json, column_mapping=source.column_mapping)
    db.add(copied)
    db.commit()
    db.refresh(copied)
    return copied


@router.put("/{workflow_id}/dag")
def update_dag(workflow_id: int, payload: DagUpdate, db: Session = Depends(get_db)):
    workflow = db.get(WorkflowDef, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    if workflow.mode != "dag":
        raise HTTPException(status_code=400, detail="只有模式 B 支持流程节点")
    node_json = payload.model_dump()
    validation = validate_dag(node_json)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail="；".join(validation["issues"]))
    workflow.node_json = node_json
    db.commit()
    db.refresh(workflow)
    return {"workflow": workflow, "validation": validation}


@router.get("/{workflow_id}/dag/validate")
def validate_workflow_dag(workflow_id: int, db: Session = Depends(get_db)):
    workflow = db.get(WorkflowDef, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return validate_dag(workflow.node_json or {})
