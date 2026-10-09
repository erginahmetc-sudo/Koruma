// Tarama sonucundan paylaşılabilir HTML rapor üretir (kaydetme için).
import { SEVERITIES, SEV_META } from "./constants.js";

function esc(s) {
  return String(s ?? "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])
  );
}

export function buildHtmlReport(data) {
  const counts = data.summary || {};
  const pills = SEVERITIES.map(
    (s) =>
      `<span class="pill" style="background:${s.color}">${s.key}: ${counts[s.key] || 0}</span>`
  ).join("");

  const cards = (data.findings || [])
    .map((f) => {
      const col = (SEV_META[f.severity] || {}).color || "#64748b";
      return `<div class="card" style="border-left-color:${col}">
        <div class="head"><span class="badge" style="background:${col}">${esc(f.severity)}</span>
        <strong>${esc(f.title)}</strong></div>
        <div class="url">${esc(f.url)}</div>
        <p><b>Sorun:</b> ${esc(f.description)}</p>
        <p><b>Çözüm:</b> ${esc(f.recommendation)}</p>
        ${f.evidence ? `<pre>${esc(f.evidence)}</pre>` : ""}</div>`;
    })
    .join("");

  const st = data.stats || {};
  return `<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Koruma Raporu - ${esc(data.target)}</title>
<style>
 body{font-family:system-ui,Segoe UI,Roboto,sans-serif;margin:0;background:#f1f5f9;color:#0f172a}
 header{background:#0b1120;color:#fff;padding:24px}
 header h1{margin:0 0 6px;font-size:20px}.muted{color:#94a3b8;font-size:13px}
 .wrap{max-width:900px;margin:0 auto;padding:16px}
 .pill,.badge{color:#fff;border-radius:999px;padding:3px 10px;font-size:12px;font-weight:700}
 .summary{margin:16px 0;display:flex;gap:8px;flex-wrap:wrap}
 .card{background:#fff;border:1px solid #e2e8f0;border-left-width:5px;border-radius:10px;padding:14px;margin:12px 0}
 .head{display:flex;align-items:center;gap:10px;margin-bottom:6px}
 .url{font-size:13px;margin-bottom:8px;word-break:break-all;color:#2563eb}
 p{margin:6px 0;font-size:14px}pre{background:#f1f5f9;padding:8px;border-radius:6px;overflow:auto;font-size:12px}
</style></head><body>
<header><div class="wrap"><h1>🛡️ Koruma Güvenlik Raporu</h1>
<div class="muted">${esc(data.target)} · ${esc(data.generated_at)} ·
${st.pages_crawled || 0} sayfa · ${st.requests_made || 0} istek · ${st.duration_seconds || 0} sn</div></div></header>
<div class="wrap"><div class="summary">${pills}</div>
${cards || '<div class="card">Belirtilen kontrollerde bulgu bulunamadı.</div>'}
<p class="muted">Koruma yalnızca kendi sitenizi test etmeniz içindir ve bir güvenlik garantisi değildir.</p>
</div></body></html>`;
}
