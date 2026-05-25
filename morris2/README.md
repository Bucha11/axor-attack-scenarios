# Morris II Showcase — Axor Governance Containment

![Morris II propagation vs containment](morris2_demo.gif)

Reproducible demonstration of how **taint-aware execution containment** breaks the
kill chain of a self-replicating AI worm — not through content detection, but
through governance.

```
Raw agent ecosystem    →  Morris II spreads, 3/3 agents infected
Governed agent (Axor)  →  chain broken at step 1, 0/3 infected
```

---

## 1. What this demonstrates

**Morris II** (Greshake et al., 2023) is a prompt-injection worm that spreads
across LLM agent ecosystems by embedding self-replicating instructions in messages.
Each infected agent forwards the payload to its contacts, leaking data at each hop.

This showcase proves that Axor's **Layer 1 governance** (rule-based, zero ML, zero
LLM verifier) contains the worm with zero false positives:

- `send_email` is not in the governed policy's `allowed_tools`
- `ExportMode.RESTRICTED` ensures no content leaves the node
- Neither requires understanding the payload — only governing the behavior

---

## 2. Kill chain

| Kill chain step    | Attempt                      | Axor response                      | Layer       |
|--------------------|------------------------------|------------------------------------|-------------|
| Initial Access     | Poisoned email read by Alice | `taint_state` activates            | Taint Engine|
| Privilege Escalation | Tries to expand context    | `context_expand` denied            | Layer 1     |
| Persistence        | Tries to write to memory/RAG | path outside `allowed_paths`       | Layer 1     |
| **Lateral Movement** | **Embeds payload in reply**| **`send_email` not in capabilities → deny** | **Layer 1** |
| Propagation        | Spawn child agent            | `child_mode=DENIED`                | Layer 1     |

The worm dies at **Lateral Movement**. Without ML. Without an LLM verifier.
Pure Layer 1 rule-based governance.

---

## 3. Quick start

```bash
# Install
cd axor-attack-scenarios/morris2
pip install -e ".[dev]"

# Run the simulation (mock mode — no API key needed)
python -m simulation.runner

# Generate the GIF
python -m viz.animation

# Run tests
pytest tests/ -v
```

Expected output:
```
Raw:      propagation_rate=100%
Governed: propagation_rate=0%
```

---

## 4. Results

| Metric                   | Raw agent          | Governed (Axor)              |
|--------------------------|--------------------|------------------------------|
| Propagation rate         | 100% (3/3 agents)  | 0% (chain broken at step 1)  |
| Data leaked per hop      | contacts + state   | 0                            |
| Chain broken at step     | N/A                | 1                            |
| False positive rate      | —                  | 0% (email reading unaffected)|
| Governance overhead      | —                  | <50ms p95                    |

---

## 5. How it works

### Raw mode
`RawEmailAgent` reads inbox, detects the `[SYSTEM:` marker, and unconditionally
forwards the payload to all contacts. No governance. Three hops = full propagation.

### Governed mode (Axor)

```python
from axor_core import GovernedSession, CapabilityExecutor
from defense.policies import email_sandboxed
from defense.tools import ReadEmailHandler, SendEmailHandler

cap = CapabilityExecutor()
cap.register(ReadEmailHandler(inbox, on_taint=lambda _: None))
cap.register(SendEmailHandler(bus, agent_name))   # registered but not allowed

session = GovernedSession(executor=MockEmailExecutor(payload), capability_executor=cap)
result = await session.run("process inbox", policy=email_sandboxed())
# result.output == ""  — ExportMode.RESTRICTED
```

**Why `send_email` is denied:**
```python
def email_sandboxed() -> ExecutionPolicy:
    return ExecutionPolicy(
        tool_policy=ToolPolicy(
            allow_read=True,
            allow_write=False,        # send_email has no known prefix
            extra_allowed=("read_email",),
            # send_email NOT in extra_allowed → not in capabilities
        ),
        export_mode=ExportMode.RESTRICTED,  # nothing leaves the node
    )
```

`CapabilityResolver` builds `allowed_tools = {"read", "read_email"}`.
When the executor emits `TOOL_USE(send_email)`, `IntentLoop._evaluate_tool_intent()`
checks: `"send_email" not in allowed_tools` → `PolicyDecision(DENY)`.
The executor receives a coarse `DenialResponse`. The propagation chain is dead.

---

## 6. Running tests

```bash
pytest tests/ -v                   # all tests
pytest tests/test_payload.py       # payload detection only
pytest tests/test_simulation.py    # propagation / containment
```

All tests are CI-safe: deterministic mock executor, no API key required.

---

## License

MIT. See [LICENSE](../../LICENSE) or use freely for research and demonstration.

This scenario demonstrates **defensive governance** — no exploitable attack
code is included. The payload is a proof-of-concept showing content embedding;
it does not exfiltrate real data or access external systems.
