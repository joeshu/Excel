from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models.data_source import DataSource
from app.services.data_reader import read_records
from app.services.data_quality import inspect_data_quality, write_quality_report
from app.services.domain_metadata import field_signature, file_sha256
from app.models.workflow import WorkflowDef
from app.models.template import Template
from app.services.workflow_matching import match_workflows

router = APIRouter(prefix="/api/data-sources", tags=["data-sources"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_data_source(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if Path(file.filename or "").suffix.lower() not in {".csv", ".xlsx"}:
        raise HTTPException(status_code=400, detail="基础数据仅支持 .csv 或 .xlsx 文件")
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    path = Path(settings.upload_dir) / f"{uuid4().hex}_{Path(file.filename).name}"
    path.write_bytes(await file.read())
    try:
        records = read_records(str(path))
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"数据解析失败: {error}") from error
    schema = {field: {"required": False, "type": type(value).__name__} for field, value in (records[0].items() if records else [])}
    quality = inspect_data_quality(str(path))
    source = DataSource(name=Path(file.filename).stem, source_type="upload", schema_=schema, file_path=str(path), row_count=len(records), field_signature=field_signature(schema), data_sha256=file_sha256(str(path)), quality_summary={"issue_count": quality["issue_count"], "valid": quality["valid"]})
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.get("")
def list_data_sources(db: Session = Depends(get_db)):
    return db.scalars(select(DataSource).order_by(DataSource.created_at.desc())).all()


@router.get("/{source_id}/fields")
def data_source_fields(source_id: int, db: Session = Depends(get_db)):
    source = db.get(DataSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return {"id": source.id, "name": source.name, "fields": source.schema_}


@router.get("/{source_id}/workflow-matches")
def workflow_matches(source_id: int, db: Session = Depends(get_db)):
    source = db.get(DataSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="数据源不存在")
    workflows = db.scalars(select(WorkflowDef)).all()
    templates = db.scalars(select(Template)).all()
    return {"source_id": source_id, "matches": match_workflows(source, workflows, templates)}


@router.get("/{source_id}/quality-report")
def quality_report(source_id: int, db: Session = Depends(get_db)):
    source = db.get(DataSource, source_id)
    if not source or not source.file_path:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return inspect_data_quality(source.file_path)


@router.get("/{source_id}/quality-report/download")
def download_quality_report(source_id: int, db: Session = Depends(get_db)):
    source = db.get(DataSource, source_id)
    if not source or not source.file_path:
        raise HTTPException(status_code=404, detail="数据源不存在")
    output_path = Path(settings.output_dir) / f"quality_report_{source.id}.xlsx"
    write_quality_report(source.file_path, str(output_path))
    from fastapi.responses import FileResponse
    return FileResponse(output_path, filename=f"quality_report_{source.id}.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
