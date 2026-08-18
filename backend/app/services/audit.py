import hashlib
import json
from pathlib import Path

from app.models.audit import AuditEvent


def sha256_file(file_path: str) -> str:
    digest = hashlib.sha256()
    with Path(file_path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record_event(db, action: str, task_id: int | None = None, batch_id: str | None = None, detail: dict | None = None) -> None:
    db.add(AuditEvent(task_id=task_id, batch_id=batch_id, action=action, detail=json.dumps(detail or {}, ensure_ascii=False)))
