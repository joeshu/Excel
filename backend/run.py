import os
import socket
import logging
from pathlib import Path
import uvicorn
from app.main import app
from app.tasks import shutdown as shutdown_tasks
from app.config import settings

Path(settings.output_dir).parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(Path(settings.output_dir).parent / "app.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


if __name__ == "__main__":
    try:
        configured_port = os.getenv("EXCEL_WORKFLOW_PORT")
        port = int(configured_port) if configured_port else find_free_port()
        logger.info("桌面应用启动，资源目录: %s", getattr(__import__("app.main", fromlist=["frontend_dist"]), "frontend_dist", "unknown"))
        logger.info("FastAPI sidecar listening on http://127.0.0.1:%s", port)
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
    except Exception:
        logger.exception("桌面应用启动失败")
        raise
    finally:
        shutdown_tasks()
