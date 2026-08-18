from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.models.data_source import DataSource
from app.models.task import TaskRecord
from app.models.workflow import WorkflowDef
from app.schemas.workflow import BatchTaskRunRequest, TaskRunRequest
from app.tasks import submit as submit_task
from app.services.formula_service import preview_formula_results

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/run", status_code=202)
def run_task(payload: TaskRunRequest, db: Session = Depends(get_db)):
    workflow = db.get(WorkflowDef, payload.workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    source = db.get(DataSource, payload.data_source_id)
    if not source:
        raise HTTPException(status_code=404, detail="数据源不存在")
    mapped_fields = set(workflow.column_mapping.values())
    source_fields = set(source.schema_)
    missing_fields = sorted(mapped_fields - source_fields)
    if missing_fields:
        raise HTTPException(status_code=400, detail=f"数据源缺少映射字段: {', '.join(missing_fields)}")
    task = TaskRecord(workflow_id=payload.workflow_id, data_source_id=payload.data_source_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    submit_task(task.id)
    return {"id": task.id, "task_id": str(task.id), "status": task.status}


@router.post("/batch-run", status_code=202)
def batch_run(payload: BatchTaskRunRequest, db: Session = Depends(get_db)):
    results = []
    for source_id in payload.data_source_ids:
        try:
            result = run_task(TaskRunRequest(workflow_id=payload.workflow_id, data_source_id=source_id), db)
            results.append({"data_source_id": source_id, **result})
        except HTTPException as error:
            results.append({"data_source_id": source_id, "status": "rejected", "error": error.detail})
    return {"tasks": results}


@router.get("/{task_id}/status")
def task_status(task_id: int, db: Session = Depends(get_db)):
    task = db.get(TaskRecord, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/{task_id}/download")
def download_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(TaskRecord, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status != "success" or not task.output_path or not Path(task.output_path).is_file():
        raise HTTPException(status_code=409, detail="任务尚未生成结果")
    return FileResponse(task.output_path, filename=f"task_{task.id}.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/{task_id}/formula-preview")
def task_formula_preview(task_id: int, limit: int = 100, db: Session = Depends(get_db)):
    task = db.get(TaskRecord, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status != "success" or not task.output_path or not Path(task.output_path).is_file():
        raise HTTPException(status_code=409, detail="任务尚未生成结果")
    return preview_formula_results(task.output_path, limit=max(1, min(limit, 1000)))


@router.get("")
def list_tasks(db: Session = Depends(get_db)):
    return db.scalars(select(TaskRecord).order_by(TaskRecord.id.desc())).all()


@router.post("/{task_id}/retry", status_code=202)
def retry_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(TaskRecord, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status not in {"failed", "success"}:
        raise HTTPException(status_code=409, detail="当前任务仍在执行")
    retry = TaskRecord(workflow_id=task.workflow_id, data_source_id=task.data_source_id)
    db.add(retry)
    db.commit()
    db.refresh(retry)
    submit_task(retry.id)
    return {"id": retry.id, "task_id": str(retry.id), "status": retry.status}
