from contextlib import asynccontextmanager
import mimetypes
from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import inspect, text

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import AuditEvent, DataSource, TaskRecord, Template, TemplateWorkbookProfile, WorkflowDef, WorkflowNode
from app.routers import data_sources, examples, formulas, tasks, templates, users, workbench, workflows
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
            if "output_sha256" not in task_columns:
                connection.execute(text("ALTER TABLE task_records ADD COLUMN output_sha256 VARCHAR(64)"))
            if "mapping_snapshot_id" not in task_columns:
                connection.execute(text("ALTER TABLE task_records ADD COLUMN mapping_snapshot_id INTEGER"))
            source_columns = {column["name"] for column in inspect(engine).get_columns("data_sources")}
            for column_name, column_sql in (("row_count", "INTEGER NOT NULL DEFAULT 0"), ("field_signature", "VARCHAR(500) NOT NULL DEFAULT ''"), ("data_sha256", "VARCHAR(64)"), ("quality_summary", "JSON NOT NULL DEFAULT '{}'")):
                if column_name not in source_columns:
                    connection.execute(text(f"ALTER TABLE data_sources ADD COLUMN {column_name} {column_sql}"))
            workflow_columns = {column["name"] for column in inspect(engine).get_columns("workflow_defs")}
            for column_name, column_sql in (("applicable_field_signature", "VARCHAR(500) NOT NULL DEFAULT ''"), ("last_used_at", "DATETIME"), ("notice_config", "JSON NOT NULL DEFAULT '{}'"), ("notice_config_version", "INTEGER NOT NULL DEFAULT 1"), ("notice_config_history", "JSON NOT NULL DEFAULT '[]'")):
                if column_name not in workflow_columns:
                    connection.execute(text(f"ALTER TABLE workflow_defs ADD COLUMN {column_name} {column_sql}"))
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
app.include_router(users.router)
app.include_router(workbench.router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok", "runtime": "local"}


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/app/", status_code=307)


def find_frontend_dist() -> Path:
    candidates = []
    if getattr(sys, "_MEIPASS", None):
        candidates.append(Path(sys._MEIPASS) / "frontend" / "dist")
    candidates.extend((Path(settings.frontend_dist), Path(sys.executable).resolve().parent / "frontend" / "dist"))
    for candidate in candidates:
        if (candidate / "index.html").is_file():
            return candidate
    return candidates[0]


frontend_dist = find_frontend_dist()


@app.get("/assets/{asset_path:path}", include_in_schema=False)
@app.get("/app/assets/{asset_path:path}", include_in_schema=False)
def frontend_asset(asset_path: str):
    asset_file = frontend_dist / "assets" / asset_path
    if not asset_file.is_file():
        raise HTTPException(status_code=404, detail=f"Frontend asset not found: {asset_path}")
    media_types = {
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".css": "text/css",
        ".json": "application/json",
        ".svg": "image/svg+xml",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
    }
    media_type = media_types.get(asset_file.suffix.lower()) or mimetypes.guess_type(asset_file.name)[0] or "application/octet-stream"
    return FileResponse(asset_file, media_type=media_type)


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
