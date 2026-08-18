from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.template import Template
from app.services.data_reader import read_records
from app.services.formula_service import find_cached_errors, inspect_formula_dependencies, inspect_formulas, python_aggregate, validate_formulas

router = APIRouter(prefix="/api/formulas", tags=["formulas"])


def template_path(template_id: int, db: Session):
    template = db.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template.file_path


@router.get("/{template_id}/inspect")
def inspect_template_formulas(template_id: int, db: Session = Depends(get_db)):
    return inspect_formulas(template_path(template_id, db))


@router.get("/{template_id}/validate")
def validate_template_formulas(template_id: int, db: Session = Depends(get_db)):
    return validate_formulas(template_path(template_id, db))


@router.get("/{template_id}/cached-errors")
def template_cached_errors(template_id: int, db: Session = Depends(get_db)):
    return find_cached_errors(template_path(template_id, db))


@router.get("/{template_id}/dependencies")
def template_formula_dependencies(template_id: int, db: Session = Depends(get_db)):
    return inspect_formula_dependencies(template_path(template_id, db))


@router.get("/{template_id}/aggregate")
def aggregate_template_data(template_id: int, data_source_id: int, group_field: str, value_field: str, db: Session = Depends(get_db)):
    from app.models.data_source import DataSource
    source = db.get(DataSource, data_source_id)
    if not source or not source.file_path:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return {"template_id": template_id, "rows": python_aggregate(read_records(source.file_path), group_field, value_field)}
