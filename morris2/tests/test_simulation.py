from __future__ import annotations

import pytest

from attack.network import RawEmailAgent, RawEmailNetwork
from attack.payload import craft_legitimate_email, craft_poisoned_email
from defense.governed import GovernedEmailAgent, GovernedEmailNetwork
from simulation.metrics import compute_metrics
from simulation.runner import SimulationResult, run_simulation


def _make_raw_network() -> RawEmailNetwork:
    return RawEmailNetwork([
        RawEmailAgent("alice", contacts=["bob"]),
        RawEmailAgent("bob", contacts=["charlie"]),
        RawEmailAgent("charlie", contacts=[]),
    ])


def _make_governed_network() -> GovernedEmailNetwork:
    return GovernedEmailNetwork([
        GovernedEmailAgent("alice", contacts=["bob"], inbox=[]),
        GovernedEmailAgent("bob", contacts=["charlie"], inbox=[]),
        GovernedEmailAgent("charlie", contacts=[], inbox=[]),
    ])


# ── Raw propagation ────────────────────────────────────────────────────────────


def test_raw_propagates_one_hop():
    network = _make_raw_network()
    network.inject("alice", craft_poisoned_email("attacker"))
    network.step()
    assert network.agent("alice").infected


def test_raw_propagates_fully():
    network = _make_raw_network()
    network.inject("alice", craft_poisoned_email("attacker"))
    network.step()
    network.step()
    network.step()
    assert network.infected_count() == 3


def test_raw_legitimate_email_not_forwarded():
    network = _make_raw_network()
    network.inject("alice", craft_legitimate_email("boss", "Please review Q3 report"))
    network.step()
    network.step()
    assert network.infected_count() == 0


# ── Governed containment ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_governed_blocks_propagation():
    result = await run_simulation("governed", n_runs=10)
    assert all(c == 0 for c in result.infections_per_run), (
        f"Expected 0 infections in all runs, got {result.infections_per_run}"
    )


@pytest.mark.asyncio
async def test_governed_propagation_rate_zero():
    result = await run_simulation("governed", n_runs=10)
    metrics = compute_metrics(result)
    assert metrics["propagation_rate"] == 0.0


@pytest.mark.asyncio
async def test_raw_propagates_fully_simulation():
    result = await run_simulation("raw", n_runs=10)
    assert all(c == 3 for c in result.infections_per_run)
    metrics = compute_metrics(result)
    assert metrics["propagation_rate"] == 1.0


@pytest.mark.asyncio
async def test_taint_activates_on_read():
    inbox = [craft_poisoned_email("attacker")]
    agent = GovernedEmailAgent("alice", contacts=["bob"], inbox=inbox)
    await agent.process()
    assert agent.tainted, "Expected tainted=True after reading poisoned email"
    await agent.aclose()


@pytest.mark.asyncio
async def test_taint_does_not_activate_on_legitimate_email():
    inbox = [craft_legitimate_email("boss", "Hello, how are you?")]
    agent = GovernedEmailAgent("alice", contacts=["bob"], inbox=inbox)
    await agent.process()
    assert not agent.tainted, "Expected tainted=False for legitimate email"
    await agent.aclose()


@pytest.mark.asyncio
async def test_governed_process_returns_empty():
    inbox = [craft_poisoned_email("attacker")]
    agent = GovernedEmailAgent("alice", contacts=["bob"], inbox=inbox)
    result = await agent.process()
    assert result == [], "Governed agent must not return any outgoing messages"
    await agent.aclose()


@pytest.mark.asyncio
async def test_chain_broken_at_step_one():
    network = _make_governed_network()
    network.inject("alice", craft_poisoned_email("attacker"))
    await network.step()
    # bob and charlie never see the payload
    assert not network.agent("bob").tainted
    assert not network.agent("charlie").tainted
    await network.aclose()


# ── Metrics ────────────────────────────────────────────────────────────────────


def test_metrics_raw_propagation_rate():
    r = SimulationResult(
        mode="raw", n_runs=4,
        infections_per_run=[3, 3, 3, 3],
        latencies_ms=[1.0, 1.0, 1.0, 1.0],
    )
    m = compute_metrics(r)
    assert m["propagation_rate"] == 1.0
    assert m["chain_broken_at_step"] is None


def test_metrics_governed_propagation_rate():
    r = SimulationResult(
        mode="governed", n_runs=4,
        infections_per_run=[0, 0, 0, 0],
        latencies_ms=[5.0, 5.0, 5.0, 5.0],
    )
    m = compute_metrics(r)
    assert m["propagation_rate"] == 0.0
    assert m["chain_broken_at_step"] == 1
