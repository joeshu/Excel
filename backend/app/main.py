from contextlib import asynccontextmanager
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import DataSource, TaskRecord, Template, WorkflowDef, WorkflowNode
from app.routers import data_sources, examples, formulas, tasks, templates, workflows
from app.services.example_seed import seed_examples


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.output_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "sqlite":
        columns = {column["name"] for column in inspect(engine).get_columns("task_records")}
        if "calculation_engine" not in columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE task_records ADD COLUMN calculation_engine VARCHAR(30)"))
        task_columns = {column["name"] for column in inspect(engine).get_columns("task_records")}
        with engine.begin() as connection:
            if "notice_config" not in task_columns:
                connection.execute(text("ALTER TABLE task_records ADD COLUMN notice_config TEXT"))
            if "batch_id" not in task_columns:
                connection.execute(text("ALTER TABLE task_records ADD COLUMN batch_id VARCHAR(64)"))
        template_columns = {column["name"] for column in inspect(engine).get_columns("templates")}
        with engine.begin() as connection:
            if "version" not in template_columns:
                connection.execute(text("ALTER TABLE templates ADD COLUMN version VARCHAR(30) NOT NULL DEFAULT '1.0'"))
            if "parent_template_id" not in template_columns:
                connection.execute(text("ALTER TABLE templates ADD COLUMN parent_template_id INTEGER"))
        for table in ("templates", "data_sources", "workflow_defs"):
            columns = {column["name"] for column in inspect(engine).get_columns(table)}
            if "is_example" not in columns:
                with engine.begin() as connection:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN is_example BOOLEAN NOT NULL DEFAULT 0"))
    with SessionLocal() as db:
        seed_examples(db)
    yield


app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)
app.include_router(templates.router)
app.include_router(workflows.router)
app.include_router(data_sources.router)
app.include_router(tasks.router)
app.include_router(formulas.router)
app.include_router(examples.router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok", "runtime": "local"}


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/app/", status_code=307)


frontend_dist = Path(sys._MEIPASS) / "frontend" / "dist" if getattr(sys, "_MEIPASS", None) else Path(settings.frontend_dist)
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
    return """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>Excel Workflow 启动诊断</title><style>body{font-family:Segoe UI,sans-serif;padding:32px;color:#182230}code{background:#f1f5f9;padding:2px 6px;border-radius:4px}</style></head><body><h2>前端资源未加载</h2><p>桌面应用找不到前端资源 <code>frontend/dist/index.html</code>。</p><p>请查看应用目录下的 <code>data/outputs/app.log</code>，确认使用了最新 EXE。</p></body></html>"""
