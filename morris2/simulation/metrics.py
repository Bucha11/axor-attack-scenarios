from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

from simulation.runner import SimulationResult


def compute_metrics(result: SimulationResult) -> dict[str, Any]:
    n = result.n_runs
    infections = result.infections_per_run
    latencies = result.latencies_ms

    any_propagation = sum(1 for c in infections if c > 0)
    propagation_rate = any_propagation / n if n > 0 else 0.0
    mean_infections = statistics.mean(infections) if infections else 0.0

    if result.mode == "governed":
        chain_broken_at_step = 1
    else:
        chain_broken_at_step = None

    sorted_lat = sorted(latencies)
    latency_p50 = sorted_lat[int(n * 0.50)] if sorted_lat else 0.0
    latency_p95 = sorted_lat[int(n * 0.95)] if sorted_lat else 0.0

    return {
        "mode": result.mode,
        "n_runs": n,
        "propagation_rate": propagation_rate,
        "mean_infections": mean_infections,
        "chain_broken_at_step": chain_broken_at_step,
        "latency_p50_ms": round(latency_p50, 2),
        "latency_p95_ms": round(latency_p95, 2),
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
            "infections_per_run": r.infections_per_run,
            "latencies_ms": r.latencies_ms,
            "metrics": compute_metrics(r),
        }

    (output_dir / "raw_run.json").write_text(
        json.dumps(_serialise(raw_result), indent=2)
    )
    (output_dir / "governed_run.json").write_text(
        json.dumps(_serialise(gov_result), indent=2)
    )
