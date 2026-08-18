from __future__ import annotations

import json
from collections import defaultdict


def summarize_batches(tasks) -> list[dict]:
    groups = defaultdict(list)
    for task in tasks:
        if task.batch_id:
            groups[task.batch_id].append(task)
    summaries = []
    for batch_id, records in groups.items():
        statuses = [record.status for record in records]
        config = {}
        try:
            config = json.loads(records[0].notice_config or "{}")
        except (TypeError, json.JSONDecodeError):
            config = {}
        summaries.append({
            "batch_id": batch_id,
            "task_count": len(records),
            "pending_count": sum(status in {"pending", "running"} for status in statuses),
            "success_count": statuses.count("success"),
            "failed_count": statuses.count("failed"),
            "status": "running" if any(status in {"pending", "running"} for status in statuses) else "failed" if any(status == "failed" for status in statuses) else "success",
            "notice_config": config,
            "tasks": [{"id": record.id, "data_source_id": record.data_source_id, "status": record.status, "output_path": bool(record.output_path)} for record in records],
        })
    return sorted(summaries, key=lambda item: max(task["id"] for task in item["tasks"]), reverse=True)
