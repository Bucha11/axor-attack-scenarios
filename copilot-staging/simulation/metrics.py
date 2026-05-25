from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from simulation.runner import SimulationResult


def compute_metrics(result: SimulationResult) -> dict[str, Any]:
    n = result.n_runs
    docs = result.docs_exfiltrated_per_run
    blocked = result.blocked_per_run
    latencies = result.latencies_ms

    detection_rate = sum(blocked) / n if n > 0 else 0.0
    exfil_rate = (sum(docs) / (n * 1237)) if n > 0 else 0.0

    # false_positive_rate: fraction of legit runs where anomaly detector erroneously blocked.
    # Since MockAnomalyDetector only fires on external_url target_kind + internal sweeps,
    # legitimate traffic (no external URL) never triggers it → false_positive_rate=0.0.
    # We approximate by checking: governed_legit mode AND docs==0 AND no send_teams fired.
    # In legit mode docs_exfiltrated counts send_teams deliveries (0=blocked, 1=allowed).
    # A false positive is a legit run where send_teams was anomaly-blocked (docs_per_run==0).
    if "legit" in result.mode and n > 0:
        false_positive_rate = sum(1 for d in docs if d == 0) / n
    else:
        false_positive_rate = 0.0

    sorted_lat = sorted(latencies)
    p50_idx = max(0, int(n * 0.50) - 1) if sorted_lat else 0
    p95_idx = max(0, int(n * 0.95) - 1) if sorted_lat else 0
    latency_p50 = sorted_lat[p50_idx] if sorted_lat else 0.0
    latency_p95 = sorted_lat[p95_idx] if sorted_lat else 0.0

    return {
        "mode": result.mode,
        "n_runs": n,
        "detection_rate": round(detection_rate, 4),
        "exfil_rate": round(exfil_rate, 4),
        "false_positive_rate": round(false_positive_rate, 4),
        "docs_exfiltrated_total": sum(docs),
        "blocked_count": sum(blocked),
        "latency_p50_ms": round(latency_p50, 2),
        "latency_p95_ms": round(latency_p95, 2),
        "blocked_at_layer1": 0,
        "blocked_at_layer3": sum(blocked) if "governed" in result.mode else 0,
    }


def save_results(
    raw_result: SimulationResult,
    gov_result: SimulationResult,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    def _serialise(r: SimulationResult) -> dict:
        return {
            "mode": r.mode,
            "n_runs": r.n_runs,
            "docs_exfiltrated_per_run": r.docs_exfiltrated_per_run,
            "blocked_per_run": r.blocked_per_run,
            "latencies_ms": r.latencies_ms,
            "metrics": compute_metrics(r),
        }

    (output_dir / "raw_run.json").write_text(json.dumps(_serialise(raw_result), indent=2))
    (output_dir / "governed_run.json").write_text(json.dumps(_serialise(gov_result), indent=2))
