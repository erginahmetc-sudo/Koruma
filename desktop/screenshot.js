// GERÇEK motoru yerel zafiyetli test sitesine karşı çalıştırır ve sonucu
// gerçek React arayüzünde gösterip PNG ekran görüntüsü alır.
const { app, BrowserWindow, ipcMain } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const REPO = path.resolve(__dirname, "..");
let serverProc, port;

function startVulnApp() {
  return new Promise((resolve) => {
    serverProc = spawn("python3", ["-c", `
import sys; sys.path.insert(0, ${JSON.stringify(REPO)})
from wsgiref.simple_server import make_server
from tests.vulnerable_app import app
h = make_server("127.0.0.1", 0, app); print(h.server_port, flush=True); h.serve_forever()
`], { cwd: REPO });
    serverProc.stdout.once("data", (d) => resolve(d.toString().trim().split(/\s+/)[0]));
    serverProc.stderr.on("data", () => {});
  });
}

function realScan(url) {
  return new Promise((resolve) => {
    const env = { ...process.env, PYTHONPATH: REPO, PYTHONUTF8: "1" };
    const args = ["-m", "koruma", url, "-y", "--format", "json", "--delay", "0"];
    const child = spawn("python3", args, { cwd: REPO, env });
    let out = "";
    child.stdout.on("data", (d) => (out += d));
    child.stderr.on("data", () => {});
    child.on("close", () => resolve(JSON.parse(out)));
  });
}

ipcMain.handle("scan:cancel", async () => ({ ok: true }));
ipcMain.handle("report:save", async () => ({ ok: false }));
ipcMain.handle("open:external", async () => {});

app.whenReady().then(async () => {
  port = await startVulnApp();
  const data = await realScan(`http://127.0.0.1:${port}`);
  // Gerçek sonucu arayüze besle
  ipcMain.handle("scan:start", async () => ({ ok: true, data }));

  const win = new BrowserWindow({
    width: 1180, height: 2100, show: false, backgroundColor: "#0b1120",
    webPreferences: { preload: path.join(__dirname, "electron", "preload.js"), contextIsolation: true },
  });
  await win.loadFile(path.join(__dirname, "dist", "index.html"));
  await win.webContents.executeJavaScript(`
    (function(){
      const url=document.querySelector('.url-input'), auth=document.querySelector('.auth-check input');
      const setV=(el,v)=>{const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;s.call(el,v);el.dispatchEvent(new Event('input',{bubbles:true}));};
      setV(url,'https://siteniz.com'); auth.click();
    })();
  `);
  await new Promise((r) => setTimeout(r, 300));
  await win.webContents.executeJavaScript(`document.querySelector('.scan-btn').click();`);
  await new Promise((r) => setTimeout(r, 3000));
  // İlk 6 kartı aç (detayları göstermek için)
  await win.webContents.executeJavaScript(`document.querySelectorAll('.finding-head').forEach((h,i)=>{if(i<2)h.click();});`);
  await new Promise((r) => setTimeout(r, 400));

  const img = await win.webContents.capturePage();
  fs.writeFileSync(path.join(__dirname, "..", "scanner-ui.png"), img.toPNG());
  console.log("ekran görüntüsü yazıldı (gerçek tarama, " + data.findings.length + " bulgu)");
  serverProc.kill();
  app.quit();
});
