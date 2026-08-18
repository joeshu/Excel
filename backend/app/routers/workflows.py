from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.template import Template
from app.models.workflow import WorkflowDef
from app.schemas.workflow import MappingUpdate, WorkflowCreate

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
    template_columns = template.column_meta.get("sheets", [{}])[0].get("columns", [])
    valid_columns = {item["column"] for item in template_columns if item.get("type") != "formula"}
    invalid_columns = sorted(set(payload.column_mapping) - valid_columns)
    empty_fields = sorted(column for column in valid_columns if not payload.column_mapping.get(column, "").strip())
    if invalid_columns:
        raise HTTPException(status_code=400, detail=f"存在不可映射的模板列: {', '.join(invalid_columns)}")
    if empty_fields:
        raise HTTPException(status_code=400, detail=f"以下模板列尚未配置数据源字段: {', '.join(empty_fields)}")
    workflow.column_mapping = payload.column_mapping
    db.commit()
    db.refresh(workflow)
    return workflow
