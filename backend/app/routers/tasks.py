from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.data_source import DataSource
from app.models.task import TaskRecord
from app.models.workflow import WorkflowDef
from app.schemas.workflow import TaskRunRequest
from app.tasks import submit as submit_task

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/run", status_code=202)
def run_task(payload: TaskRunRequest, db: Session = Depends(get_db)):
    if not db.get(WorkflowDef, payload.workflow_id):
        raise HTTPException(status_code=404, detail="工作流不存在")
    if not db.get(DataSource, payload.data_source_id):
        raise HTTPException(status_code=404, detail="数据源不存在")
    task = TaskRecord(workflow_id=payload.workflow_id, data_source_id=payload.data_source_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    submit_task(task.id)
    return {"id": task.id, "task_id": str(task.id), "status": task.status}


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
