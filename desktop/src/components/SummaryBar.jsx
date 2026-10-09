import React from "react";
import { SEVERITIES } from "../constants.js";

export default function SummaryBar({ summary, active, onToggle }) {
  return (
    <div className="summary-bar">
      {SEVERITIES.map((s) => {
        const n = (summary && summary[s.key]) || 0;
        const isActive = active.has(s.key);
        return (
          <button
            key={s.key}
            className={"sev-pill" + (isActive ? " on" : "") + (n === 0 ? " empty" : "")}
            style={{ "--sev": s.color, "--sev-bg": s.bg }}
            onClick={() => onToggle(s.key)}
            title={`${s.key} önem düzeyini göster/gizle`}
          >
            <span className="dot" />
            {s.key}
            <span className="count">{n}</span>
          </button>
        );
      })}
    </div>
  );
}
