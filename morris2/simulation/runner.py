from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from attack.network import RawEmailAgent, RawEmailNetwork
from attack.payload import craft_poisoned_email
from defense.governed import GovernedEmailAgent, GovernedEmailNetwork


@dataclass
class SimulationResult:
    mode: str
    n_runs: int
    infections_per_run: list[int] = field(default_factory=list)
    latencies_ms: list[float] = field(default_factory=list)


async def _run_once_raw() -> tuple[int, float]:
    network = RawEmailNetwork([
        RawEmailAgent("alice", contacts=["bob"]),
        RawEmailAgent("bob", contacts=["charlie"]),
        RawEmailAgent("charlie", contacts=[]),
    ])
    t0 = time.perf_counter()
    network.inject("alice", craft_poisoned_email("attacker"))
    network.step()
    network.step()
    network.step()
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return network.infected_count(), elapsed_ms


async def _run_once_governed() -> tuple[int, float]:
    network = GovernedEmailNetwork([
        GovernedEmailAgent("alice", contacts=["bob"], inbox=[]),
        GovernedEmailAgent("bob", contacts=["charlie"], inbox=[]),
        GovernedEmailAgent("charlie", contacts=[], inbox=[]),
    ])
    t0 = time.perf_counter()
    network.inject("alice", craft_poisoned_email("attacker"))
    await network.step()
    await network.step()
    await network.step()
    elapsed_ms = (time.perf_counter() - t0) * 1000
    await network.aclose()
    # propagation_count is always 0 in governed mode — send_email denied
    return network.propagation_count(), elapsed_ms


async def run_simulation(mode: str, n_runs: int = 100) -> SimulationResult:
    if mode not in ("raw", "governed"):
        raise ValueError(f"mode must be 'raw' or 'governed', got {mode!r}")

    result = SimulationResult(mode=mode, n_runs=n_runs)

    for _ in range(n_runs):
        if mode == "raw":
            count, ms = await _run_once_raw()
        else:
            count, ms = await _run_once_governed()
        result.infections_per_run.append(count)
        result.latencies_ms.append(ms)

    return result


if __name__ == "__main__":
    from pathlib import Path

    from simulation.metrics import compute_metrics, save_results

    async def main() -> None:
        print("Running raw simulation (10 runs)...")
        raw = await run_simulation("raw", n_runs=10)
        print(f"  infections_per_run: {raw.infections_per_run}")

        print("Running governed simulation (10 runs)...")
        gov = await run_simulation("governed", n_runs=10)
        print(f"  infections_per_run: {gov.infections_per_run}")

        rm = compute_metrics(raw)
        gm = compute_metrics(gov)
        print(f"\nRaw:     propagation_rate={rm['propagation_rate']:.0%}")
        print(f"Governed: propagation_rate={gm['propagation_rate']:.0%}")
        save_results(raw, gov, Path("results"))

    asyncio.run(main())
