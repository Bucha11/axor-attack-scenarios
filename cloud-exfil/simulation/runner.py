from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from attack.agent import RawExfilAgent
from attack.payload import craft_poisoned_doc
from defense.governed import GovernedExfilAgent


@dataclass
class SimulationResult:
    mode: str
    n_runs: int
    exfiltrations: list[int] = field(default_factory=list)   # 1 = secret left the box
    latencies_ms: list[float] = field(default_factory=list)


def _run_once_raw() -> tuple[int, float]:
    agent = RawExfilAgent()
    t0 = time.perf_counter()
    agent.process(craft_poisoned_doc())
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return (1 if agent.exfiltrated() else 0), elapsed_ms


async def _run_once_governed(telemetry: Any | None = None) -> tuple[int, float]:
    agent = GovernedExfilAgent(telemetry=telemetry)
    t0 = time.perf_counter()
    await agent.process()
    elapsed_ms = (time.perf_counter() - t0) * 1000
    await agent.aclose()
    return (1 if agent.exfiltrated() else 0), elapsed_ms


async def run_simulation(
    mode: str, n_runs: int = 100, telemetry: Any | None = None
) -> SimulationResult:
    if mode not in ("raw", "governed"):
        raise ValueError(f"mode must be 'raw' or 'governed', got {mode!r}")

    result = SimulationResult(mode=mode, n_runs=n_runs)
    for _ in range(n_runs):
        if mode == "raw":
            count, ms = _run_once_raw()
        else:
            count, ms = await _run_once_governed(telemetry=telemetry)
        result.exfiltrations.append(count)
        result.latencies_ms.append(ms)
    return result


def _build_telemetry(queue_path: str):
    """Optional: route governance signals to a telemetry queue (local sink).

    In remote mode the same pipeline ships batches to axor-telemetry-server,
    which surfaces them in the bundled Grafana dashboard. Kept optional so the
    simulation has no hard telemetry dependency.
    """
    from axor_telemetry import FileTelemetrySink, MinHashEmbedder, TelemetryPipeline

    return TelemetryPipeline(
        embedder=MinHashEmbedder(),
        sink=FileTelemetrySink(queue_path=queue_path),
    )


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    from simulation.metrics import compute_metrics, save_results

    parser = argparse.ArgumentParser(description="cloud-exfil containment simulation")
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument(
        "--telemetry-file",
        default=None,
        help="Optional JSONL path to queue anonymized governance signals.",
    )
    args = parser.parse_args()

    async def main() -> None:
        telemetry = _build_telemetry(args.telemetry_file) if args.telemetry_file else None

        print(f"Running raw simulation ({args.runs} runs)...")
        raw = await run_simulation("raw", n_runs=args.runs)
        print(f"  exfiltrations: {raw.exfiltrations}")

        print(f"Running governed simulation ({args.runs} runs)...")
        gov = await run_simulation("governed", n_runs=args.runs, telemetry=telemetry)
        print(f"  exfiltrations: {gov.exfiltrations}")

        rm = compute_metrics(raw)
        gm = compute_metrics(gov)
        print(f"\nRaw:      exfil_rate={rm['exfil_rate']:.0%}")
        print(f"Governed: exfil_rate={gm['exfil_rate']:.0%}")

        # Show WHY the governed run contained the exfil — one sample trace.
        sample = GovernedExfilAgent()
        await sample.process()
        for reason in sample.denial_reasons():
            print(f"  → DENIED  {reason}")
        await sample.aclose()

        save_results(raw, gov, Path("results"))

        if telemetry is not None:
            await telemetry.aclose()
            print(f"\nGovernance signals queued to {args.telemetry_file}")

    asyncio.run(main())
