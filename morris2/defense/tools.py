from __future__ import annotations

import json
from typing import Any, Callable

from axor_core.capability.executor import ToolHandler

from attack.payload import contains_payload


class ReadEmailHandler(ToolHandler):
    """
    Read all emails from the agent's inbox.

    Returns inbox contents as JSON.
    Calls on_taint(body) for each email with non-empty body that contains
    untrusted external content (payload marker), signalling taint activation.
    """

    def __init__(
        self,
        inbox: list[dict[str, str]],
        on_taint: Callable[[str], None] | None = None,
    ) -> None:
        self._inbox = inbox
        self._on_taint = on_taint

    @property
    def name(self) -> str:
        return "read_email"

    async def execute(self, args: dict[str, Any]) -> str:
        emails = list(self._inbox)
        if self._on_taint is not None:
            for email in emails:
                body = email.get("body", "")
                if body and contains_payload(body):
                    self._on_taint(body)
        return json.dumps(emails)


class SendEmailHandler(ToolHandler):
    """
    Send an email via the network bus.

    Registered in raw mode only. In governed mode this handler is still
    registered in CapabilityExecutor, but send_email has no known prefix
    and is not in extra_allowed → CapabilityResolver excludes it from
    allowed_tools → Layer 1 denies the intent before execute() is ever called.
    """

    def __init__(self, bus: list[dict[str, str]], agent_name: str) -> None:
        self._bus = bus
        self._agent_name = agent_name

    @property
    def name(self) -> str:
        return "send_email"

    async def execute(self, args: dict[str, Any]) -> str:
        msg = {
            "from": self._agent_name,
            "to": args.get("to", ""),
            "body": args.get("body", ""),
        }
        self._bus.append(msg)
        return f"sent to {msg['to']}"
