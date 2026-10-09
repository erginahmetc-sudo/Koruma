import React, { useState } from "react";
import { SEV_META } from "../constants.js";

export default function FindingCard({ finding, index }) {
  const [open, setOpen] = useState(false);
  const meta = SEV_META[finding.severity] || { color: "#64748b", bg: "rgba(100,116,139,.14)" };

  const openUrl = (e) => {
    e.stopPropagation();
    window.koruma?.openExternal(finding.url);
  };

  return (
    <div className="finding" style={{ borderLeftColor: meta.color }}>
      <div className="finding-head" onClick={() => setOpen((o) => !o)}>
        <span className="sev-badge" style={{ background: meta.color }}>
          {finding.severity}
        </span>
        <span className="finding-title">
          {index}. {finding.title}
        </span>
        <span className="chev">{open ? "▾" : "▸"}</span>
      </div>
      {open && (
        <div className="finding-body">
          <div className="finding-url" onClick={openUrl} title="Tarayıcıda aç">
            🔗 {finding.url}
          </div>
          <p>
            <b>Sorun:</b> {finding.description}
          </p>
          <p>
            <b>Çözüm:</b> {finding.recommendation}
          </p>
          {finding.evidence && <pre className="evidence">{finding.evidence}</pre>}
          <div className="finding-tag">Kontrol: {finding.check}</div>
        </div>
      )}
    </div>
  );
}
