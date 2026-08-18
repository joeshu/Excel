from __future__ import annotations

import json
from collections import defaultdict

from app.services.data_quality import inspect_data_quality


def summarize_batches(tasks, data_sources=None) -> list[dict]:
    groups = defaultdict(list)
    for task in tasks:
        if task.batch_id:
            groups[task.batch_id].append(task)
    summaries = []
    for batch_id, records in groups.items():
        statuses = [record.status for record in records]
        try:
            config = json.loads(records[0].notice_config or "{}")
        except (TypeError, json.JSONDecodeError):
            config = {}
        quality_reports = []
        if data_sources:
            for record in records:
                source = data_sources.get(record.data_source_id)
                if source and source.file_path:
                    try:
                        quality_reports.append(inspect_data_quality(source.file_path))
                    except (OSError, ValueError):
                        continue
        quality_issue_count = sum(report["issue_count"] for report in quality_reports)
        summaries.append({
            "batch_id": batch_id,
            "task_count": len(records),
            "pending_count": sum(status in {"pending", "running"} for status in statuses),
            "success_count": statuses.count("success"),
            "failed_count": statuses.count("failed"),
            "status": "running" if any(status in {"pending", "running"} for status in statuses) else "failed" if any(status == "failed" for status in statuses) else "success",
            "notice_config": config,
            "quality_issue_count": quality_issue_count,
            "quality_invalid_count": sum(not report["valid"] for report in quality_reports),
            "quality_checked_count": len(quality_reports),
            "tasks": [{"id": record.id, "data_source_id": record.data_source_id, "status": record.status, "output_path": bool(record.output_path), "output_sha256": getattr(record, "output_sha256", None)} for record in records],
        })
    return sorted(summaries, key=lambda item: max(task["id"] for task in item["tasks"]), reverse=True)


def failed_tasks(tasks):
    return [task for task in tasks if task.status == "failed"]
