from sqlalchemy import select

from app.models.data_source import DataSource
from app.models.task import TaskRecord
from app.models.template import Template
from app.models.workflow import WorkflowDef


def build_workbench_summary(db) -> dict:
    templates = db.scalars(select(Template)).all()
    workflows = db.scalars(select(WorkflowDef)).all()
    sources = db.scalars(select(DataSource)).all()
    tasks = db.scalars(select(TaskRecord).order_by(TaskRecord.id.desc())).all()
    return {
        "counts": {
            "templates": len(templates),
            "workflows": len(workflows),
            "data_sources": len(sources),
            "successful_tasks": sum(task.status == "success" for task in tasks),
        },
        "attention": {
            "failed_tasks": sum(task.status == "failed" for task in tasks),
            "quality_issues": sum((source.quality_summary or {}).get("issue_count", 0) for source in sources),
            "running_tasks": sum(task.status in {"pending", "running"} for task in tasks),
        },
        "recent_tasks": [
            {"id": task.id, "status": task.status, "workflow_id": task.workflow_id, "data_source_id": task.data_source_id, "finished_at": task.finished_at}
            for task in tasks[:8]
        ],
    }
