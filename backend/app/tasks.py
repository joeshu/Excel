from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor
import threading
from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.database import SessionLocal
from app.models.data_source import DataSource
from app.models.task import TaskRecord
from app.models.template import Template
from app.models.workflow import WorkflowDef
from app.services.data_reader import read_records
from app.services.workflow_engine import WorkflowEngine
from app.services.formula_service import validate_formulas
from app.services.recalculation import recalculate
from app.services.dag_engine import execute_dag
from app.services.final_workbook import append_final_sheets


executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="excel-worker")
executor_lock = threading.Lock()
executor_closed = False


def generate_excel(task_id: int) -> int:
    db = SessionLocal()
    task = db.get(TaskRecord, task_id)
    try:
        task.status = "running"
        task.started_at = datetime.utcnow()
        db.commit()
        workflow = db.get(WorkflowDef, task.workflow_id)
        source = db.get(DataSource, task.data_source_id)
        template = db.get(Template, workflow.template_id)
        records = read_records(source.file_path)
        output_path = str(Path(settings.output_dir) / f"task_{task.id}_{uuid4().hex}.xlsx")
        if workflow.mode == "dag":
            execute_dag(workflow.node_json or {}, records, template.file_path, output_path)
        elif workflow.mode == "formula":
            engine = WorkflowEngine(template.file_path)
            engine.execute_formula_mode(records, workflow.column_mapping)
            engine.save(output_path)
        else:
            raise ValueError("当前任务模式不支持执行")
        notice_config = json.loads(task.notice_config or "{}")
        append_final_sheets(output_path, records, workflow, template, source, notice_config)
        formula_validation = validate_formulas(output_path)
        if not formula_validation["valid"]:
            task.error_log = "；".join(issue["message"] for issue in formula_validation["issues"])
            task.status = "failed"
            task.finished_at = datetime.utcnow()
            db.commit()
            raise ValueError(task.error_log)
        recalculation = recalculate(output_path)
        task.calculation_engine = recalculation.engine
        task.error_log = recalculation.message
        task.status = "success"
        task.output_path = output_path
        task.finished_at = datetime.utcnow()
        db.commit()
        return task.id
    except Exception as error:
        task.status = "failed"
        task.error_log = str(error)
        task.finished_at = datetime.utcnow()
        db.commit()
        raise
    finally:
        db.close()


def submit(task_id: int) -> None:
    executor.submit(generate_excel, task_id)


def shutdown() -> None:
    global executor_closed
    with executor_lock:
        if executor_closed:
            return
        executor_closed = True
        executor.shutdown(wait=False, cancel_futures=True)
