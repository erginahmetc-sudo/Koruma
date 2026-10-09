const { app, BrowserWindow, ipcMain, shell, dialog } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");
const os = require("os");

const isDev = process.env.KORUMA_DEV === "1";
let mainWindow = null;
let currentScan = null; // çalışan tarama süreci (iptal için)

function resolvePython() {
  // Windows'ta "py -3" veya "python", diğerlerinde "python3" denenir.
  if (process.env.KORUMA_PYTHON) return [process.env.KORUMA_PYTHON];
  if (process.platform === "win32") return ["py", "python", "python3"];
  return ["python3", "python"];
}

// Python motorunun (koruma paketi) bulunacağı kök dizin + PYTHONPATH.
function engineRoot() {
  if (isDev) return path.resolve(__dirname, "..", "..");
  // Paketlenmiş uygulamada koruma, extraResources ile resources/engine altına kopyalanır.
  return path.join(process.resourcesPath, "engine");
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1180,
    height: 820,
    minWidth: 900,
    minHeight: 640,
    backgroundColor: "#0b1120",
    title: "Koruma",
    icon: path.join(__dirname, "..", "build", "icon.png"),
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  mainWindow.setMenuBarVisibility(false);

  if (isDev) {
    mainWindow.loadURL("http://localhost:5123");
    mainWindow.webContents.openDevTools({ mode: "detach" });
  } else {
    mainWindow.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  }

  // Harici bağlantıları sistem tarayıcısında aç (uygulama içinde değil).
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// Python yorumlayıcısını bulmak için her adayı -V ile dener.
function pickPython(candidates) {
  return new Promise((resolve) => {
    const tryNext = (i) => {
      if (i >= candidates.length) return resolve(null);
      const cmd = candidates[i];
      const probe = spawn(cmd, ["-c", "import sys; print(sys.version)"]);
      let ok = false;
      probe.on("error", () => tryNext(i + 1));
      probe.on("exit", (code) => {
        if (code === 0) {
          ok = true;
          resolve(cmd);
        } else if (!ok) {
          tryNext(i + 1);
        }
      });
    };
    tryNext(0);
  });
}

function buildArgs(opts) {
  const args = ["-m", "koruma", opts.url, "-y", "--progress-json", "--format", "json"];
  if (opts.checks && opts.checks.length) args.push("--checks", opts.checks.join(","));
  if (opts.maxPages) args.push("--max-pages", String(opts.maxPages));
  if (typeof opts.delay === "number") args.push("--delay", String(opts.delay));
  if (opts.insecure) args.push("--insecure");
  if (opts.testPostForms) args.push("--test-post-forms");
  if (opts.online) args.push("--online");
  for (const c of opts.cookies || []) if (c.trim()) args.push("--cookie", c.trim());
  for (const h of opts.headers || []) if (h.trim()) args.push("--header", h.trim());
  return args;
}

ipcMain.handle("scan:start", async (event, opts) => {
  if (currentScan) return { ok: false, error: "Zaten bir tarama çalışıyor." };

  const py = await pickPython(resolvePython());
  if (!py) {
    return {
      ok: false,
      error:
        "Python bulunamadı. Lütfen Python 3.9+ kurun (python.org) ve 'requests' ile " +
        "'beautifulsoup4' paketlerini yükleyin:  pip install requests beautifulsoup4",
    };
  }

  const root = engineRoot();
  const env = { ...process.env, PYTHONPATH: root + path.delimiter + (process.env.PYTHONPATH || ""),
                PYTHONIOENCODING: "utf-8", PYTHONUTF8: "1" };

  const args = buildArgs(opts);
  const send = (channel, payload) => {
    if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send(channel, payload);
  };

  return new Promise((resolve) => {
    let child;
    try {
      child = spawn(py, args, { cwd: root, env });
    } catch (e) {
      return resolve({ ok: false, error: "Tarama başlatılamadı: " + e.message });
    }
    currentScan = child;

    let stdout = "";
    let stderrTail = "";
    let buf = "";

    child.stdout.on("data", (d) => (stdout += d.toString("utf-8")));

    // İlerleme: stderr'deki '@@KORUMA@@{json}' satırları.
    child.stderr.on("data", (d) => {
      buf += d.toString("utf-8");
      let idx;
      while ((idx = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, idx);
        buf = buf.slice(idx + 1);
        const PREFIX = "@@KORUMA@@";
        const at = line.indexOf(PREFIX);
        if (at >= 0) {
          try {
            const obj = JSON.parse(line.slice(at + PREFIX.length));
            if (obj.msg) send("scan:progress", obj.msg);
          } catch (_) { /* yoksay */ }
        } else {
          stderrTail = (stderrTail + line + "\n").slice(-2000);
        }
      }
    });

    child.on("error", (e) => {
      currentScan = null;
      resolve({ ok: false, error: "Çalıştırma hatası: " + e.message });
    });

    child.on("close", (code, signal) => {
      currentScan = null;
      if (signal) return resolve({ ok: false, cancelled: true, error: "Tarama iptal edildi." });
      try {
        const data = JSON.parse(stdout);
        resolve({ ok: true, data });
      } catch (e) {
        resolve({
          ok: false,
          error:
            "Sonuç ayrıştırılamadı (çıkış kodu " + code + ").\n" +
            (stderrTail.trim() || stdout.slice(0, 500) || "Bilinmeyen hata."),
        });
      }
    });
  });
});

ipcMain.handle("scan:cancel", async () => {
  if (currentScan) {
    currentScan.kill();
    return { ok: true };
  }
  return { ok: false };
});

// Raporu dosyaya kaydet (HTML veya JSON).
ipcMain.handle("report:save", async (event, { content, format }) => {
  const ext = format === "html" ? "html" : "json";
  const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, {
    title: "Raporu kaydet",
    defaultPath: path.join(os.homedir(), `koruma-rapor.${ext}`),
    filters: [{ name: ext.toUpperCase(), extensions: [ext] }],
  });
  if (canceled || !filePath) return { ok: false };
  fs.writeFileSync(filePath, content, "utf-8");
  return { ok: true, filePath };
});

ipcMain.handle("open:external", async (event, url) => {
  if (/^https?:\/\//i.test(url)) await shell.openExternal(url);
});

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
