import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.services.example_seed import example_root

router = APIRouter(prefix="/api/examples", tags=["examples"])


@router.get("/tutorials")
def list_tutorials():
    root = example_root()
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise HTTPException(status_code=404, detail="示例教程不存在")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tutorials = []
    for scenario in manifest.get("scenarios", []):
        tutorial_name = scenario.get("tutorial")
        if not tutorial_name:
            continue
        tutorial_path = root / "tutorials" / tutorial_name
        if tutorial_path.is_file():
            tutorials.append({"scenario": scenario["name"], "complexity": scenario["complexity"], "title": tutorial_name.removesuffix(".md"), "content": tutorial_path.read_text(encoding="utf-8")})
    return {"tutorials": tutorials}
