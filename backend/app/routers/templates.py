from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.template import Template
from app.services.template_parser import TemplateParser, ensure_xlsx

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_template(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        ensure_xlsx(file.filename or "")
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    path = Path(settings.upload_dir) / f"{uuid4().hex}_{Path(file.filename).name}"
    path.write_bytes(await file.read())
    try:
        metadata = TemplateParser().parse(str(path))
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"模板解析失败: {error}") from error
    template = Template(name=Path(file.filename).stem, file_path=str(path), has_formula=metadata["has_formula"], column_meta=metadata, sheet_count=metadata["sheet_count"])
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("")
def list_templates(db: Session = Depends(get_db)):
    return db.scalars(select(Template).order_by(Template.created_at.desc())).all()


@router.get("/{template_id}/columns")
def template_columns(template_id: int, db: Session = Depends(get_db)):
    template = db.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template.column_meta
