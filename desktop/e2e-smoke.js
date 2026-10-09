// Electron ana süreç mantığını (Python motorunu spawn edip JSON ayrıştırma)
// gerçek bir pencere açmadan, yerel zafiyetli test sunucusuna karşı doğrular.
const { spawn } = require("child_process");
const path = require("path");
const http = require("http");

const REPO = path.resolve(__dirname, "..");

// 1) Zafiyetli test uygulamasını Python'da ayağa kaldır (rastgele port).
const server = spawn("python3", ["-c", `
import sys; sys.path.insert(0, ${JSON.stringify(REPO)})
from wsgiref.simple_server import make_server
from tests.vulnerable_app import app
httpd = make_server("127.0.0.1", 0, app)
print(httpd.server_port, flush=True)
httpd.serve_forever()
`], { cwd: REPO });

let port = "";
server.stdout.once("data", (d) => {
  port = d.toString().trim().split(/\s+/)[0];
  runScan(`http://127.0.0.1:${port}`);
});
server.stderr.on("data", () => {}); // WSGI günlüğünü yut

function runScan(url) {
  const env = { ...process.env, PYTHONPATH: REPO, PYTHONUTF8: "1" };
  const args = ["-m", "koruma", url, "-y", "--progress-json", "--format", "json", "--delay", "0"];
  const child = spawn("python3", args, { cwd: REPO, env });

  let stdout = "", buf = "", progressCount = 0;
  child.stdout.on("data", (d) => (stdout += d));
  child.stderr.on("data", (d) => {
    buf += d.toString();
    let i;
    while ((i = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, i); buf = buf.slice(i + 1);
      const at = line.indexOf("@@KORUMA@@");
      if (at >= 0) { try { JSON.parse(line.slice(at + 10)); progressCount++; } catch {} }
    }
  });

  child.on("close", (code) => {
    server.kill();
    let data;
    try { data = JSON.parse(stdout); }
    catch (e) { console.error("FAIL: stdout JSON ayrıştırılamadı"); process.exit(1); }

    const titles = data.findings.map((f) => f.title);
    const need = [
      ["XSS", (t) => t.includes("XSS")],
      ["SQL", (t) => t.includes("SQL")],
      ["dizin geçişi/LFI", (t) => t.toLowerCase().includes("dosya yolu")],
      ["açık yönlendirme", (t) => t.toLowerCase().includes("yönlendirme")],
      ["eksik CSP", (t) => t.includes("Content-Security-Policy")],
    ];
    const missing = need.filter(([, f]) => !titles.some(f)).map(([n]) => n);

    console.log(`çıkış kodu       : ${code}`);
    console.log(`ilerleme olayı   : ${progressCount}`);
    console.log(`toplam bulgu     : ${data.findings.length}`);
    console.log(`özet             : ${JSON.stringify(data.summary)}`);
    if (missing.length) {
      console.error("FAIL: beklenen bulgular eksik -> " + missing.join(", "));
      process.exit(1);
    }
    if (progressCount < 3) { console.error("FAIL: ilerleme olayları gelmedi"); process.exit(1); }
    console.log("\n✓ E2E PIPELINE OK — motor, JSON çıktı ve ilerleme akışı çalışıyor.");
    process.exit(0);
  });
}

setTimeout(() => { console.error("FAIL: zaman aşımı"); server.kill(); process.exit(1); }, 30000);
