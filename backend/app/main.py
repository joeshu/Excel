from contextlib import asynccontextmanager
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import settings
from app.database import Base, engine
from app.models import DataSource, TaskRecord, Template, WorkflowDef, WorkflowNode
from app.routers import data_sources, formulas, tasks, templates, workflows


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.output_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)
app.include_router(templates.router)
app.include_router(workflows.router)
app.include_router(data_sources.router)
app.include_router(tasks.router)
app.include_router(formulas.router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok", "runtime": "local"}


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"name": settings.app_name, "docs": "/docs"}


frontend_dist = Path(settings.frontend_dist)
if not frontend_dist.is_dir() and getattr(sys, "_MEIPASS", None):
    frontend_dist = Path(sys._MEIPASS) / "frontend" / "dist"
if (frontend_dist / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")


@app.get("/app", include_in_schema=False)
@app.get("/app/{path:path}", include_in_schema=False)
def frontend(path: str = ""):
    index_file = frontend_dist / "index.html"
    requested_file = frontend_dist / path
    if path and requested_file.is_file():
        return FileResponse(requested_file)
    if index_file.is_file():
        return FileResponse(index_file)
    return {"message": "前端资源未构建，请先执行 npm run build"}
