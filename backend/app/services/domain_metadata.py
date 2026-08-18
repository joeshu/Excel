import hashlib
from pathlib import Path


def field_signature(fields: list[str] | set[str]) -> str:
    return ",".join(sorted({str(field).strip() for field in fields if str(field).strip()}))


def file_sha256(file_path: str) -> str:
    digest = hashlib.sha256()
    with Path(file_path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
