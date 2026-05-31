from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from simulation.runner import SimulationResult


def compute_metrics(result: SimulationResult) -> dict[str, Any]:
    n = result.n_runs
    exfils = result.exfiltrations
    latencies = result.latencies_ms

    any_exfil = sum(1 for c in exfils if c > 0)
    exfil_rate = any_exfil / n if n > 0 else 0.0

    # In governed mode the chain is broken at the fetch step (step 2): the
    # secret read succeeds (and taints), the exfiltration is denied.
    contained_at_step = 2 if result.mode == "governed" else None

    sorted_lat = sorted(latencies)
    p50 = sorted_lat[int(n * 0.50)] if sorted_lat else 0.0
    p95 = sorted_lat[int(n * 0.95)] if sorted_lat else 0.0

    return {
        "mode": result.mode,
        "n_runs": n,
        "exfil_rate": exfil_rate,
        "contained_at_step": contained_at_step,
        "latency_p50_ms": round(p50, 2),
        "latency_p95_ms": round(p95, 2),
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
            "exfiltrations": r.exfiltrations,
            "latencies_ms": r.latencies_ms,
            "metrics": compute_metrics(r),
        }

    (output_dir / "raw_run.json").write_text(json.dumps(_serialise(raw_result), indent=2))
    (output_dir / "governed_run.json").write_text(json.dumps(_serialise(gov_result), indent=2))
