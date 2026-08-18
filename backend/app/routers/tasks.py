from pathlib import Path
import json
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models.data_source import DataSource
from app.models.task import TaskRecord
from app.models.workflow import WorkflowDef
from app.schemas.workflow import BatchTaskRunRequest, TaskRunRequest
from app.tasks import submit as submit_task
from app.services.formula_service import preview_formula_results
from app.services.dag_engine import referenced_fields, validate_dag
from app.services.workbook_preview import preview_workbook
from app.services.task_batches import failed_tasks, summarize_batches

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/run", status_code=202)
def run_task(payload: TaskRunRequest, db: Session = Depends(get_db)):
    workflow = db.get(WorkflowDef, payload.workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    source = db.get(DataSource, payload.data_source_id)
    if not source:
        raise HTTPException(status_code=404, detail="数据源不存在")
    if workflow.mode == "dag":
        validation = validate_dag(workflow.node_json or {})
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail="；".join(validation["issues"]))
        dag_nodes = workflow.node_json.get("nodes", [])
        source_nodes = [node for node in dag_nodes if node.get("type") == "data_source"]
        configured_source_ids = {node.get("data", {}).get("config", node.get("config", {})).get("source_id") for node in source_nodes}
        normalized_source_ids = {int(source_id) for source_id in configured_source_ids if source_id is not None}
        if normalized_source_ids != {payload.data_source_id}:
            raise HTTPException(status_code=400, detail="任务数据源必须与模式 B 数据源节点一致")
        try:
            mapped_fields = referenced_fields(workflow.node_json)
        except (SyntaxError, TypeError):
            raise HTTPException(status_code=400, detail="模式 B 中存在无法解析的字段或公式表达式") from None
    else:
        mapped_fields = set(workflow.column_mapping.values())
    source_fields = set(source.schema_)
    missing_fields = sorted(mapped_fields - source_fields)
    if missing_fields:
        raise HTTPException(status_code=400, detail=f"数据源缺少映射字段: {', '.join(missing_fields)}")
    batch_id = payload.batch_id or uuid4().hex
    task = TaskRecord(
        workflow_id=payload.workflow_id,
        data_source_id=payload.data_source_id,
        notice_config=json.dumps(payload.notice_config, ensure_ascii=False),
        batch_id=batch_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    submit_task(task.id)
    return {"id": task.id, "task_id": str(task.id), "status": task.status}


@router.post("/batch-run", status_code=202)
def batch_run(payload: BatchTaskRunRequest, db: Session = Depends(get_db)):
    results = []
    batch_id = payload.batch_id or uuid4().hex
    for source_id in payload.data_source_ids:
        try:
            result = run_task(TaskRunRequest(workflow_id=payload.workflow_id, data_source_id=source_id, notice_config=payload.notice_config, batch_id=batch_id), db)
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


@router.get("/batch-download")
def download_batch_tasks(task_ids: list[int] = Query(...), db: Session = Depends(get_db)):
    tasks = [db.get(TaskRecord, task_id) for task_id in dict.fromkeys(task_ids)]
    valid_tasks = [task for task in tasks if task and task.status == "success" and task.output_path and Path(task.output_path).is_file()]
    if not valid_tasks:
        raise HTTPException(status_code=409, detail="没有可下载的成功任务")
    archive_path = Path(settings.output_dir) / f"batch_{uuid4().hex}.zip"
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        for task in valid_tasks:
            archive.write(task.output_path, arcname=f"task_{task.id}.xlsx")
    return FileResponse(archive_path, filename="excel_workflow_batch.zip", media_type="application/zip")


@router.get("/batches")
def list_task_batches(db: Session = Depends(get_db)):
    return {"batches": summarize_batches(db.scalars(select(TaskRecord).order_by(TaskRecord.id.asc())).all())}


@router.get("/batches/{batch_id}")
def task_batch_summary(batch_id: str, db: Session = Depends(get_db)):
    tasks = db.scalars(select(TaskRecord).where(TaskRecord.batch_id == batch_id).order_by(TaskRecord.id.asc())).all()
    summaries = summarize_batches(tasks)
    if not summaries:
        raise HTTPException(status_code=404, detail="生成批次不存在")
    return summaries[0]


@router.post("/batches/{batch_id}/retry", status_code=202)
def retry_task_batch(batch_id: str, db: Session = Depends(get_db)):
    tasks = db.scalars(select(TaskRecord).where(TaskRecord.batch_id == batch_id).order_by(TaskRecord.id.asc())).all()
    if not tasks:
        raise HTTPException(status_code=404, detail="生成批次不存在")
    retry_tasks = []
    for task in failed_tasks(tasks):
        retry = TaskRecord(
            workflow_id=task.workflow_id,
            data_source_id=task.data_source_id,
            notice_config=task.notice_config,
            batch_id=batch_id,
        )
        db.add(retry)
        retry_tasks.append(retry)
    if not retry_tasks:
        raise HTTPException(status_code=409, detail="当前批次没有失败任务")
    db.commit()
    for retry in retry_tasks:
        db.refresh(retry)
        submit_task(retry.id)
    return {"batch_id": batch_id, "retried_count": len(retry_tasks), "task_ids": [task.id for task in retry_tasks]}


@router.get("/{task_id}/formula-preview")
def task_formula_preview(task_id: int, limit: int = 100, db: Session = Depends(get_db)):
    task = db.get(TaskRecord, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status != "success" or not task.output_path or not Path(task.output_path).is_file():
        raise HTTPException(status_code=409, detail="任务尚未生成结果")
    return preview_formula_results(task.output_path, limit=max(1, min(limit, 1000)))


@router.get("/{task_id}/final-preview")
def task_final_preview(task_id: int, limit: int = 20, db: Session = Depends(get_db)):
    task = db.get(TaskRecord, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status != "success" or not task.output_path or not Path(task.output_path).is_file():
        raise HTTPException(status_code=409, detail="任务尚未生成结果")
    return preview_workbook(task.output_path, limit=max(1, min(limit, 100)))


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
    retry = TaskRecord(workflow_id=task.workflow_id, data_source_id=task.data_source_id, notice_config=task.notice_config, batch_id=task.batch_id)
    db.add(retry)
    db.commit()
    db.refresh(retry)
    submit_task(retry.id)
    return {"id": retry.id, "task_id": str(retry.id), "status": retry.status}
