from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.workbench import build_workbench_summary

router = APIRouter(prefix="/api/workbench", tags=["workbench"])


@router.get("/summary")
def workbench_summary(db: Session = Depends(get_db)):
    return build_workbench_summary(db)
