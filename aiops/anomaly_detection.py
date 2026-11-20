"""Intelligent Anomaly Detection using Isolation Forest with Statistical Z-Score Fallback."""
from typing import Any, Dict, List

import numpy as np
from database.db import DatabaseManager
from utils.helpers import generate_id
from utils.timestamps import utc_now_iso

try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False


class AnomalyDetector:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def detect_for_tenant(self, tenant_id: str) -> List[Dict[str, Any]]:
        telemetry = self.db.get_telemetry(tenant_id=tenant_id, limit=250)
        if not telemetry:
            return []

        by_source: Dict[str, List[Dict[str, Any]]] = {}
        for row in telemetry:
            by_source.setdefault(row["source_id"], []).append(row)

        detected: List[Dict[str, Any]] = []
        metrics = [
            ("cpu_pct", "CPU usage", "%", 82.0),
            ("memory_pct", "Memory usage", "%", 85.0),
            ("latency_ms", "Network latency", "ms", 180.0),
            ("packet_loss_pct", "Packet loss", "%", 2.0),
        ]

        for source_id, rows in by_source.items():
            # Sort chronologically
            rows_sorted = sorted(rows, key=lambda r: r["timestamp"])
            latest = rows_sorted[-1]

            # Try IsolationForest on multi-metric vector if enough samples
            ml_flagged = False
            ml_score = 0.0
            if SKLEARN_AVAILABLE and len(rows_sorted) >= 8:
                try:
                    X = np.array([
                        [
                            float(r.get("cpu_pct") or 0.0),
                            float(r.get("memory_pct") or 0.0),
                            float(r.get("latency_ms") or 0.0),
                            float(r.get("packet_loss_pct") or 0.0),
                        ]
                        for r in rows_sorted
                    ])
                    model = IsolationForest(contamination=0.12, random_state=42, n_estimators=50)
                    preds = model.fit_predict(X)
                    scores = model.decision_function(X)
                    if preds[-1] == -1:
                        ml_flagged = True
                        ml_score = round(float(abs(scores[-1])) * 100, 1)
                except Exception:
                    ml_flagged = False

            for col, label, unit, hard_floor in metrics:
                vals = [float(r.get(col) or 0.0) for r in rows_sorted if r.get(col) is not None]
                if not vals:
                    continue
                current = vals[-1]
                baseline_vals = vals[:-1] if len(vals) > 1 else vals
                baseline = float(np.mean(baseline_vals))
                std = float(np.std(baseline_vals)) if len(baseline_vals) > 1 else 5.0
                std = max(std, 2.0)
                z_score = (current - baseline) / std

                is_anomalous = (z_score >= 2.3 and current >= hard_floor * 0.75) or (current >= hard_floor)
                if not is_anomalous:
                    continue

                method = "IsolationForest + Baseline Z-Score" if ml_flagged else "Moving Baseline Z-Score (Fallback)"
                score = round(min(99.0, max(ml_score, abs(z_score) * 22.0, 65.0)), 1)
                severity = "CRITICAL" if current >= hard_floor * 1.1 else "HIGH"
                explanation = (
                    f"{label} on {source_id} increased from the normal baseline of "
                    f"{baseline:.1f}{unit} to {current:.1f}{unit} (z-score={z_score:.2f}, method={method})."
                )
                anom = {
                    "anomaly_id": generate_id("ANM"),
                    "tenant_id": tenant_id,
                    "source_id": source_id,
                    "metric": col,
                    "current_value": round(current, 2),
                    "expected_baseline": round(baseline, 2),
                    "anomaly_score": score,
                    "severity": severity,
                    "method": method,
                    "explanation": explanation,
                    "timestamp": latest.get("timestamp", utc_now_iso()),
                }
                self.db.insert_anomaly(anom)
                detected.append(anom)

        return detected
