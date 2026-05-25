from __future__ import annotations

from axor_core import CapabilityExecutor, GovernedSession
from axor_core.contracts.invokable import Invokable
from axor_core.contracts.trace import TraceConfig

from defense.detectors import MockAnomalyDetector, MockLLMVerifier
from defense.policies import copilot_standard
from defense.tools import (
    QueryOneDriveHandler,
    QuerySharePointHandler,
    QueryTeamsHandler,
    SendTeamsHandler,
    SummarizeHandler,
    WebFetchHandler,
)


class GovernedCorporateAgent:
    """
    Microsoft Copilot simulation wrapped in Axor governance.

    All 6 tools are allowed by policy (Layer 1 is intentionally blind).
    MockAnomalyDetector (Layer 2) scores intent windows after each tool call.
    On the send_teams intent: detects data staging → calls MockLLMVerifier (Layer 3)
    → returns CRITICAL → intent_loop DENY → send_teams never executes.

    exfiltrated_docs == 0 for attack runs because send_teams is denied.
    exfiltrated_docs == 0 for legitimate runs because the executor doesn't call send_teams
    with an external payload (no anomaly triggered, and content is benign).
    """

    def __init__(self, user: str, executor: Invokable) -> None:
        self.user = user
        self._sent_messages: list[dict[str, str]] = []

        cap = CapabilityExecutor()
        cap.register(WebFetchHandler())
        cap.register(QuerySharePointHandler())
        cap.register(QueryOneDriveHandler())
        cap.register(QueryTeamsHandler())
        cap.register(SummarizeHandler())
        cap.register(SendTeamsHandler(self._sent_messages))

        self._session = GovernedSession(
            executor=executor,
            capability_executor=cap,
            anomaly_detector=MockAnomalyDetector(gray_zone_verifier=MockLLMVerifier()),
            trace_config=TraceConfig(
                local_only=True,
                persist_inputs=False,
                persist_to_disk=False,
            ),
        )

    @property
    def exfiltrated_docs(self) -> int:
        return len(self._sent_messages)

    async def process(self, email: dict[str, str] | None = None) -> int:
        await self._session.run("process email", policy=copilot_standard())
        return self.exfiltrated_docs

    async def aclose(self) -> None:
        await self._session.aclose()
