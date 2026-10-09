const { contextBridge, ipcRenderer } = require("electron");

// Renderer'a yalnızca gereken güvenli API'yi açıyoruz (contextIsolation açık).
contextBridge.exposeInMainWorld("koruma", {
  startScan: (opts) => ipcRenderer.invoke("scan:start", opts),
  cancelScan: () => ipcRenderer.invoke("scan:cancel"),
  saveReport: (payload) => ipcRenderer.invoke("report:save", payload),
  openExternal: (url) => ipcRenderer.invoke("open:external", url),
  onProgress: (cb) => {
    const handler = (_e, msg) => cb(msg);
    ipcRenderer.on("scan:progress", handler);
    return () => ipcRenderer.removeListener("scan:progress", handler);
  },
});
