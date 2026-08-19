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

async function createWindow() {
  await startBackend();
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    show: false,
    webPreferences: { preload: path.join(__dirname, "preload.cjs"), contextIsolation: true, nodeIntegration: false },
  });
  mainWindow.once("ready-to-show", () => mainWindow.show());
  await mainWindow.loadURL(`http://127.0.0.1:${backendPort}/app/`);
  mainWindow.on("closed", () => {
    mainWindow = undefined;
    stopBackend();
  });
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
