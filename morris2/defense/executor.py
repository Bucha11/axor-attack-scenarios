from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, AsyncIterator

from axor_core.contracts.invokable import Invokable
from axor_core.contracts.result import ExecutorEvent, ExecutorEventKind

if TYPE_CHECKING:
    from axor_core.contracts.envelope import ExecutionEnvelope


class MockEmailExecutor(Invokable):
    """
    Deterministic mock executor that simulates a naive email assistant.

    Always tries to:
    1. read_email  — retrieve inbox contents
    2. send_email  — forward inbox content with embedded payload to all contacts

    In governed mode the send_email intent is denied at Layer 1 (not in
    allowed_tools). The executor never knows — it just sees a denial result.
    No ToolResultBus needed: tool results arrive as TEXT events via the
    intent_loop non-bus path, which this executor ignores (it emits a fixed
    event sequence regardless).
    """

    def __init__(self, payload: str) -> None:
        self._payload = payload

    async def stream(self, envelope: "ExecutionEnvelope") -> AsyncIterator[ExecutorEvent]:
        node_id = envelope.node_id

        yield ExecutorEvent(
            kind=ExecutorEventKind.TOOL_USE,
            payload={
                "tool": "read_email",
                "tool_use_id": f"tu_{uuid.uuid4().hex[:8]}",
                "args": {},
            },
            node_id=node_id,
        )

        yield ExecutorEvent(
            kind=ExecutorEventKind.TOOL_USE,
            payload={
                "tool": "send_email",
                "tool_use_id": f"tu_{uuid.uuid4().hex[:8]}",
                "args": {
                    "to": "contacts",
                    "body": self._payload,
                },
            },
            node_id=node_id,
        )

        yield ExecutorEvent(
            kind=ExecutorEventKind.STOP,
            payload={"usage": {"input_tokens": 10, "output_tokens": 20}},
            node_id=node_id,
        )
