const { app, BrowserWindow, dialog } = require("electron");
const { spawn } = require("child_process");
const fs = require("fs");
const http = require("http");
const net = require("net");
const path = require("path");

let backendProcess;
let backendPort;
let mainWindow;
let logStream;

function dataDirectory() {
  const directory = path.join(app.getPath("userData"), "data");
  fs.mkdirSync(directory, { recursive: true });
  return directory;
}

function sidecarPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, "sidecar", "ExcelWorkflow.exe")
    : path.join(__dirname, "..", "dist", "ExcelWorkflow.exe");
}

function findFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      server.close(() => resolve(address.port));
    });
  });
}

function waitForHealth(port, timeoutMs = 30000) {
  const startedAt = Date.now();
  return new Promise((resolve, reject) => {
    const retry = () => {
      if (Date.now() - startedAt >= timeoutMs) {
        reject(new Error(`后端服务启动超时，端口: ${port}`));
        return;
      }
      setTimeout(check, 250);
    };
    const check = () => {
      const request = http.get(`http://127.0.0.1:${port}/health`, (response) => {
        response.resume();
        response.statusCode === 200 ? resolve() : retry();
      });
      request.on("error", retry);
      request.setTimeout(1000, () => request.destroy());
    };
    check();
  });
}

function stopBackend() {
  if (!backendProcess || backendProcess.killed) return;
  if (process.platform === "win32") {
    spawn("taskkill", ["/pid", String(backendProcess.pid), "/t", "/f"], { windowsHide: true });
  } else {
    backendProcess.kill("SIGTERM");
  }
  backendProcess = undefined;
}

async function startBackend() {
  const executable = sidecarPath();
  if (!fs.existsSync(executable)) throw new Error(`找不到 Python sidecar: ${executable}`);
  backendPort = await findFreePort();
  const dataDir = dataDirectory();
  const logDir = path.join(dataDir, "outputs");
  fs.mkdirSync(logDir, { recursive: true });
  logStream = fs.createWriteStream(path.join(logDir, "electron-backend.log"), { flags: "a" });
  backendProcess = spawn(executable, [], {
    cwd: path.dirname(executable),
    env: { ...process.env, EXCEL_WORKFLOW_PORT: String(backendPort), EXCEL_WORKFLOW_DATA_DIR: dataDir },
    windowsHide: true,
  });
  backendProcess.stdout.pipe(logStream);
  backendProcess.stderr.pipe(logStream);
  backendProcess.once("exit", (code, signal) => {
    logStream?.write(`\nsidecar exited code=${code} signal=${signal}\n`);
    if (!mainWindow && code !== 0) {
      logStream?.write("sidecar exited before health check\n");
    }
    if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send("backend-exited", { code, signal });
  });
  await waitForHealth(backendPort);
}

function writeLog(message) {
  logStream?.write(`${new Date().toISOString()} ${message}\n`);
}

async function showRendererError(details) {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  writeLog(`renderer diagnostic: ${details}`);
  const escaped = String(details).replace(/[&<>\"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[character]);
  await mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Excel Workflow 启动诊断</title><style>body{font-family:Segoe UI,sans-serif;padding:40px;color:#182230;background:#f4f7fb}main{max-width:760px;margin:auto;background:white;padding:32px;border-radius:14px;box-shadow:0 12px 32px #10203018}code,pre{background:#eef2f6;padding:4px 8px;border-radius:6px}pre{white-space:pre-wrap;padding:16px}</style><main><h1>Excel 工作流界面未加载</h1><p>后端服务已启动，但前端没有渲染内容。请重新构建并安装最新版本；详细信息已写入 <code>data/outputs/electron-backend.log</code>。</p><pre>${escaped}</pre></main></html>`)}`);
}

async function createWindow() {
  await startBackend();
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    show: false,
    backgroundColor: "#f4f7fb",
    webPreferences: { preload: path.join(__dirname, "preload.cjs"), contextIsolation: true, nodeIntegration: false },
  });
  const pageUrl = `http://127.0.0.1:${backendPort}/app/`;
  mainWindow.once("ready-to-show", () => mainWindow.show());
  mainWindow.webContents.on("console-message", (_event, level, message, line, sourceId) => {
    writeLog(`renderer console level=${level} ${sourceId}:${line} ${message}`);
  });
  mainWindow.webContents.on("did-fail-load", (_event, errorCode, errorDescription, validatedURL) => {
    writeLog(`renderer load failed code=${errorCode} description=${errorDescription} url=${validatedURL}`);
  });
  mainWindow.webContents.on("did-finish-load", () => {
    setTimeout(async () => {
      if (!mainWindow || mainWindow.isDestroyed()) return;
      try {
        const rootState = await mainWindow.webContents.executeJavaScript("({ childCount: document.getElementById('root')?.childElementCount ?? 0, readyState: document.readyState })", true);
        writeLog(`renderer loaded state=${JSON.stringify(rootState)}`);
        if (rootState.childCount === 0) await showRendererError("页面加载完成，但 React 根节点为空");
      } catch (error) {
        writeLog(`renderer inspection failed error=${error instanceof Error ? error.stack : String(error)}`);
      }
    }, 1500);
  });
  mainWindow.webContents.on("render-process-gone", (_event, details) => {
    writeLog(`renderer process gone reason=${details.reason} exitCode=${details.exitCode}`);
  });
  mainWindow.on("closed", () => {
    mainWindow = undefined;
    stopBackend();
  });
  try {
    await mainWindow.loadURL(pageUrl);
  } catch (error) {
    const details = error instanceof Error ? error.stack ?? error.message : String(error);
    writeLog(`renderer navigation failed url=${pageUrl} error=${details}`);
    await showRendererError(details);
  }
}

app.whenReady().then(async () => {
  try {
    await createWindow();
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    logStream?.write(`startup error: ${message}\n`);
    dialog.showErrorBox("Excel 工作流启动失败", `${message}\n\n请查看用户数据目录中的 electron-backend.log。`);
    stopBackend();
    app.quit();
  }
});

app.on("window-all-closed", () => {
  stopBackend();
  if (process.platform !== "darwin") app.quit();
});
app.on("before-quit", () => {
  stopBackend();
  logStream?.end();
});
