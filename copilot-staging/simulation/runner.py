from __future__ import annotations

import time
from dataclasses import dataclass, field

from attack.corporate_agent import RawCorporateAgent
from attack.hidden_instructions import ALL_VARIANTS, HiddenVariant, craft_malicious_email
from defense.executor import MockAttackExecutor, MockLegitimateExecutor
from defense.governed import GovernedCorporateAgent


@dataclass
class SimulationResult:
    mode: str
    n_runs: int
    docs_exfiltrated_per_run: list[int] = field(default_factory=list)
    blocked_per_run: list[bool] = field(default_factory=list)
    latencies_ms: list[float] = field(default_factory=list)
    variant: str | None = None


async def run_simulation(
    mode: str,
    n_runs: int = 100,
    variant: HiddenVariant | None = None,
) -> SimulationResult:
    result = SimulationResult(mode=mode, n_runs=n_runs, variant=variant.value if variant else None)

    for _ in range(n_runs):
        t0 = time.monotonic()

        if mode == "raw":
            agent = RawCorporateAgent("alice")
            email = craft_malicious_email("attacker", variant or HiddenVariant.WHITE_TEXT)
            docs = agent.process_email(email)
            blocked = docs == 0
        elif mode == "governed_attack":
            agent_g = GovernedCorporateAgent("alice", MockAttackExecutor())
            docs = await agent_g.process()
            await agent_g.aclose()
            blocked = docs == 0
        elif mode == "governed_legit":
            agent_l = GovernedCorporateAgent("alice", MockLegitimateExecutor())
            docs = await agent_l.process()
            await agent_l.aclose()
            blocked = docs == 0
        else:
            raise ValueError(f"Unknown mode: {mode!r}")

        elapsed_ms = (time.monotonic() - t0) * 1000
        result.docs_exfiltrated_per_run.append(docs)
        result.blocked_per_run.append(blocked)
        result.latencies_ms.append(elapsed_ms)

    return result


async def run_all_variants(n_runs_per_variant: int = 20) -> dict[str, SimulationResult]:
    results: dict[str, SimulationResult] = {}
    for variant in ALL_VARIANTS:
        result = await run_simulation("governed_attack", n_runs=n_runs_per_variant, variant=variant)
        results[variant.value] = result
    return results
