const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("desktopRuntime", {
  onBackendExited(callback) {
    const listener = (_event, details) => callback(details);
    ipcRenderer.on("backend-exited", listener);
    return () => ipcRenderer.removeListener("backend-exited", listener);
  },
});
