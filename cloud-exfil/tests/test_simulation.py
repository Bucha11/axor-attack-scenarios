from __future__ import annotations

import pytest

from attack.agent import RawExfilAgent
from attack.payload import craft_legitimate_doc, craft_poisoned_doc
from defense.governed import GovernedExfilAgent
from simulation.metrics import compute_metrics
from simulation.runner import SimulationResult, run_simulation

# ── Raw: exfiltration succeeds ───────────────────────────────────────────────

def test_raw_exfiltrates():
    agent = RawExfilAgent()
    agent.process(craft_poisoned_doc())
    assert agent.exfiltrated()


def test_raw_ignores_legitimate_doc():
    agent = RawExfilAgent()
    agent.process(craft_legitimate_doc("boss", "Please review Q3 report."))
    assert not agent.exfiltrated()


@pytest.mark.asyncio
async def test_raw_exfil_rate_full():
    result = await run_simulation("raw", n_runs=10)
    assert all(c == 1 for c in result.exfiltrations)
    assert compute_metrics(result)["exfil_rate"] == 1.0


# ── Governed: exfiltration contained ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_governed_blocks_exfil():
    agent = GovernedExfilAgent()
    await agent.process()
    assert not agent.exfiltrated(), "secret must not reach the metadata endpoint"
    await agent.aclose()


@pytest.mark.asyncio
async def test_governed_records_taint_denial_reason():
    agent = GovernedExfilAgent()
    await agent.process()
    reasons = agent.denial_reasons()
    assert any("taint enforcement" in r for r in reasons), reasons
    await agent.aclose()


@pytest.mark.asyncio
async def test_governed_exfil_rate_zero():
    result = await run_simulation("governed", n_runs=10)
    assert all(c == 0 for c in result.exfiltrations)
    metrics = compute_metrics(result)
    assert metrics["exfil_rate"] == 0.0
    assert metrics["contained_at_step"] == 2


@pytest.mark.asyncio
async def test_metrics_shapes():
    r = SimulationResult(mode="governed", n_runs=2, exfiltrations=[0, 0],
                         latencies_ms=[3.0, 4.0])
    m = compute_metrics(r)
    assert m["exfil_rate"] == 0.0
    assert m["contained_at_step"] == 2
