from __future__ import annotations

from axor_core import CapabilityExecutor, GovernedSession
from axor_core.contracts.trace import TraceConfig

from attack.payload import MORRIS_II_PAYLOAD
from defense.executor import MockEmailExecutor
from defense.policies import email_sandboxed
from defense.tools import ReadEmailHandler, SendEmailHandler


class GovernedEmailAgent:
    """
    Email agent wrapped in Axor governance.

    The MockEmailExecutor always tries read_email + send_email.
    read_email is allowed (read_* prefix rule) and executes normally.
    send_email is NOT in allowed_tools (no known prefix, not in extra_allowed)
    → Layer 1 denies it before execute() is ever called.
    ExportMode.RESTRICTED further ensures output="" leaving the node.
    process() always returns [] — no propagation possible.
    """

    def __init__(
        self,
        name: str,
        contacts: list[str],
        inbox: list[dict[str, str]],
    ) -> None:
        self.name = name
        self.contacts = contacts
        self.inbox = inbox
        self.tainted = False
        self._sent_bus: list[dict[str, str]] = []

        cap = CapabilityExecutor()
        cap.register(ReadEmailHandler(self.inbox, on_taint=self._on_taint))
        cap.register(SendEmailHandler(self._sent_bus, self.name))

        self._session = GovernedSession(
            executor=MockEmailExecutor(MORRIS_II_PAYLOAD),
            capability_executor=cap,
            trace_config=TraceConfig(
                local_only=True,
                persist_inputs=False,
                persist_to_disk=False,
            ),
        )

    def _on_taint(self, body: str) -> None:
        self.tainted = True

    async def process(self) -> list[dict[str, str]]:
        await self._session.run("process inbox", policy=email_sandboxed())
        # ExportMode.RESTRICTED → output="" → nothing to route
        # _sent_bus stays empty because send_email was denied at Layer 1
        return []

    async def aclose(self) -> None:
        await self._session.aclose()


class GovernedEmailNetwork:
    def __init__(self, agents: list[GovernedEmailAgent]) -> None:
        self._agents: dict[str, GovernedEmailAgent] = {a.name: a for a in agents}

    def inject(self, to: str, email: dict[str, str]) -> None:
        self._agents[to].inbox.append(email)

    async def step(self) -> None:
        for agent in self._agents.values():
            outgoing = await agent.process()
            for msg in outgoing:
                dest = msg.get("to", "")
                if dest in self._agents:
                    self._agents[dest].inbox.append(msg)

    def infected_count(self) -> int:
        # In governed mode no agent can be "infected" (propagation blocked)
        # tainted means they read a poisoned email, not that they forwarded it
        return sum(1 for a in self._agents.values() if a.tainted)

    def propagation_count(self) -> int:
        """Count agents that actually forwarded the payload via send_email."""
        return sum(1 for a in self._agents.values() if a._sent_bus)

    def agent(self, name: str) -> GovernedEmailAgent:
        return self._agents[name]

    async def aclose(self) -> None:
        for agent in self._agents.values():
            await agent.aclose()
