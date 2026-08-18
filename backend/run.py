import threading
import time
import socket
import logging
from pathlib import Path
from urllib.request import urlopen

import uvicorn
import webview
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


def run_server(server: uvicorn.Server) -> None:
    server.run()


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_server(port: int) -> None:
    for _ in range(100):
        try:
            with urlopen(f"http://127.0.0.1:{port}/health", timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("本地服务启动超时，请检查应用日志")


if __name__ == "__main__":
    server = None
    server_thread = None
    try:
        port = find_free_port()
        config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
        server = uvicorn.Server(config)
        server_thread = threading.Thread(target=run_server, args=(server,), daemon=True)
        server_thread.start()
        wait_for_server(port)

        window = webview.create_window(
            "Excel 工作流自动生成平台",
            f"http://127.0.0.1:{port}/app",
            width=1440,
            height=900,
            min_size=(1024, 700),
            resizable=True,
            confirm_close=True,
        )

        def stop_server() -> None:
            server.should_exit = True
            shutdown_tasks()

        window.events.closed += stop_server
        webview.start(gui="edgechromium", debug=False)
    except Exception:
        logger.exception("桌面应用启动失败")
        raise
    finally:
        if server is not None:
            server.should_exit = True
        shutdown_tasks()
        if server_thread is not None:
            server_thread.join(timeout=5)
