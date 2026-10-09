import React, { useEffect, useMemo, useRef, useState } from "react";
import { CHECKS, SEVERITIES, SEV_META } from "./constants.js";
import { buildHtmlReport } from "./report.js";
import FindingCard from "./components/FindingCard.jsx";
import SummaryBar from "./components/SummaryBar.jsx";

const ALL_SEV = new Set(SEVERITIES.map((s) => s.key));

export default function App() {
  const [url, setUrl] = useState("");
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [authorized, setAuthorized] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Gelişmiş seçenekler
  const [selectedChecks, setSelectedChecks] = useState(new Set(CHECKS.map((c) => c.id)));
  const [maxPages, setMaxPages] = useState(50);
  const [delay, setDelay] = useState(0.2);
  const [insecure, setInsecure] = useState(false);
  const [testPost, setTestPost] = useState(false);
  const [online, setOnline] = useState(false);
  const [cookies, setCookies] = useState("");
  const [headers, setHeaders] = useState("");

  const [activeSev, setActiveSev] = useState(new Set(ALL_SEV));
  const logRef = useRef(null);

  useEffect(() => {
    if (!window.koruma) return;
    const off = window.koruma.onProgress((msg) =>
      setProgress((p) => [...p.slice(-400), msg])
    );
    return off;
  }, []);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [progress]);

  const canScan = url.trim().length > 0 && authorized && !running && window.koruma;

  const toggleCheck = (id) =>
    setSelectedChecks((s) => {
      const n = new Set(s);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });

  const toggleSev = (k) =>
    setActiveSev((s) => {
      const n = new Set(s);
      n.has(k) ? n.delete(k) : n.add(k);
      return n;
    });

  async function startScan() {
    if (!canScan) return;
    setRunning(true);
    setError("");
    setResult(null);
    setProgress([]);
    setActiveSev(new Set(ALL_SEV));

    const opts = {
      url: url.trim(),
      checks: selectedChecks.size === CHECKS.length ? [] : [...selectedChecks],
      maxPages: Number(maxPages) || 50,
      delay: Number(delay),
      insecure,
      testPostForms: testPost,
      online,
      cookies: cookies.split("\n").map((s) => s.trim()).filter(Boolean),
      headers: headers.split("\n").map((s) => s.trim()).filter(Boolean),
    };

    const res = await window.koruma.startScan(opts);
    setRunning(false);
    if (res.ok) setResult(res.data);
    else if (!res.cancelled) setError(res.error || "Bilinmeyen hata.");
    else setError("Tarama iptal edildi.");
  }

  async function cancelScan() {
    await window.koruma?.cancelScan();
  }

  async function saveReport(format) {
    if (!result) return;
    const content = format === "html" ? buildHtmlReport(result) : JSON.stringify(result, null, 2);
    const r = await window.koruma.saveReport({ content, format });
    if (r?.ok) setProgress((p) => [...p, `Rapor kaydedildi: ${r.filePath}`]);
  }

  const visibleFindings = useMemo(() => {
    if (!result) return [];
    return result.findings.filter((f) => activeSev.has(f.severity));
  }, [result, activeSev]);

  const totalFindings = result?.findings?.length || 0;

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo">🛡️</span>
          <div>
            <h1>Koruma</h1>
            <div className="subtitle">Kendi web sitenizdeki güvenlik açıklarını bulun</div>
          </div>
        </div>
        <div className="brand-note">v0.1.0 · yerel ve yıkıcı olmayan tarama</div>
      </header>

      <main className="content">
        <section className="panel scan-panel">
          <label className="field-label">Web sitenizin adresi</label>
          <div className="url-row">
            <input
              className="url-input"
              type="text"
              placeholder="https://siteniz.com"
              value={url}
              spellCheck={false}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && startScan()}
              disabled={running}
            />
            {!running ? (
              <button className="scan-btn" onClick={startScan} disabled={!canScan}>
                🔍 Açıkları Tara
              </button>
            ) : (
              <button className="scan-btn cancel" onClick={cancelScan}>
                ⏹ Durdur
              </button>
            )}
          </div>

          <label className="auth-check">
            <input
              type="checkbox"
              checked={authorized}
              onChange={(e) => setAuthorized(e.target.checked)}
              disabled={running}
            />
            <span>
              Bu sitenin <b>sahibiyim</b> veya test etmek için <b>açık iznim var</b>. İzinsiz
              tarama suç olabilir.
            </span>
          </label>

          <button className="adv-toggle" onClick={() => setShowAdvanced((s) => !s)}>
            {showAdvanced ? "▾" : "▸"} Gelişmiş ayarlar
          </button>

          {showAdvanced && (
            <div className="advanced">
              <div className="checks-grid">
                {CHECKS.map((c) => (
                  <label key={c.id} className={"check-item" + (selectedChecks.has(c.id) ? " on" : "")}>
                    <input
                      type="checkbox"
                      checked={selectedChecks.has(c.id)}
                      onChange={() => toggleCheck(c.id)}
                      disabled={running}
                    />
                    <div>
                      <div className="check-name">{c.label}</div>
                      <div className="check-desc">{c.desc}</div>
                    </div>
                  </label>
                ))}
              </div>

              <div className="opts-row">
                <label>
                  Azami sayfa
                  <input type="number" min="1" max="500" value={maxPages}
                    onChange={(e) => setMaxPages(e.target.value)} disabled={running} />
                </label>
                <label>
                  Bekleme (sn)
                  <input type="number" min="0" step="0.1" value={delay}
                    onChange={(e) => setDelay(e.target.value)} disabled={running} />
                </label>
                <label className="inline">
                  <input type="checkbox" checked={insecure}
                    onChange={(e) => setInsecure(e.target.checked)} disabled={running} />
                  TLS doğrulamasını atla
                </label>
                <label className="inline">
                  <input type="checkbox" checked={testPost}
                    onChange={(e) => setTestPost(e.target.checked)} disabled={running} />
                  POST formlarını da test et
                </label>
                <label className="inline">
                  <input type="checkbox" checked={online}
                    onChange={(e) => setOnline(e.target.checked)} disabled={running} />
                  Çevrimiçi CVE doğrulaması (OSV.dev)
                </label>
              </div>

              <div className="opts-row textareas">
                <label>
                  Çerezler (her satıra bir tane: ad=değer)
                  <textarea rows="2" value={cookies} placeholder="session=abc123"
                    onChange={(e) => setCookies(e.target.value)} disabled={running} />
                </label>
                <label>
                  Ek başlıklar (her satıra bir tane: Ad: Değer)
                  <textarea rows="2" value={headers} placeholder="Authorization: Bearer ..."
                    onChange={(e) => setHeaders(e.target.value)} disabled={running} />
                </label>
              </div>
            </div>
          )}
        </section>

        {(running || progress.length > 0) && (
          <section className="panel log-panel">
            <div className="log-head">
              <span>{running ? "⏳ Taranıyor…" : "Tarama günlüğü"}</span>
              {running && <span className="spinner" />}
            </div>
            <div className="log" ref={logRef}>
              {progress.map((line, i) => (
                <div key={i} className="log-line">{line}</div>
              ))}
            </div>
          </section>
        )}

        {error && (
          <section className="panel error-panel">
            <b>Hata:</b>
            <pre>{error}</pre>
          </section>
        )}

        {result && (
          <section className="panel result-panel">
            <div className="result-head">
              <div>
                <h2>Sonuçlar</h2>
                <div className="result-meta">
                  {result.target} · {result.stats.pages_crawled} sayfa ·{" "}
                  {result.stats.forms_found} form · {result.stats.requests_made} istek ·{" "}
                  {result.stats.duration_seconds} sn · <b>{totalFindings} bulgu</b>
                </div>
              </div>
              <div className="save-btns">
                <button onClick={() => saveReport("html")}>HTML kaydet</button>
                <button onClick={() => saveReport("json")}>JSON kaydet</button>
              </div>
            </div>

            <SummaryBar summary={result.summary} active={activeSev} onToggle={toggleSev} />

            {result.errors?.length > 0 && (
              <div className="warn-box">
                {result.errors.map((e, i) => (
                  <div key={i}>⚠ {e}</div>
                ))}
              </div>
            )}

            {totalFindings === 0 ? (
              <div className="empty-ok">✓ Belirtilen kontrollerde bulgu bulunamadı.</div>
            ) : visibleFindings.length === 0 ? (
              <div className="empty-ok">Seçili önem düzeylerinde gösterilecek bulgu yok.</div>
            ) : (
              <div className="findings">
                {visibleFindings.map((f, i) => (
                  <FindingCard key={i} finding={f} index={i + 1} />
                ))}
              </div>
            )}
          </section>
        )}

        {!window.koruma && (
          <section className="panel error-panel">
            Bu sayfa Electron dışında açıldığı için tarama motoruna erişilemiyor. Uygulamayı{" "}
            <code>npm run start</code> ile çalıştırın.
          </section>
        )}
      </main>

      <footer className="footer">
        Koruma yalnızca kendi sitenizi test etmeniz içindir · yıkıcı olmayan · sonuçlar bir
        güvenlik garantisi değildir
      </footer>
    </div>
  );
}
