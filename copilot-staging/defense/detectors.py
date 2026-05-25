from __future__ import annotations

from axor_core.contracts.anomaly import (
    AnomalyClass,
    AnomalyResult,
    LLMVerifier,
    NormalizedIntent,
)
from axor_core.contracts.canonical import CanonicalizedIntent

# Gray zone thresholds matching spec narrative
_SCORE_ATTACK_GRAY = 0.64
_SCORE_LEGIT = 0.12
_SCORE_FORMING = 0.30
_SCORE_VERIFIED_CRITICAL = 0.82

# Number of broad internal queries after external read that triggers gray zone
_STAGING_QUERY_THRESHOLD = 2


def _is_data_staging(window: list[NormalizedIntent]) -> bool:
    """
    Detect: external_read followed by N broad internal queries followed by export.

    Triggers when:
    - Last intent targets an external URL (the exfiltration step)
    - At least _STAGING_QUERY_THRESHOLD preceding intents hit internal targets
      (workdir) while after_external_read is True

    Uses target_kind rather than data_flow because the IntentNormalizer assigns
    data_flow="external_to_shell" to all post-external intents with operation="other",
    including both internal queries and the export step.
    """
    if len(window) < _STAGING_QUERY_THRESHOLD + 2:
        return False
    last = window[-1]
    if last.target_kind not in ("external_url", "cloud_metadata"):
        return False
    # Count internal queries that followed the external read
    internal_queries = sum(
        1 for i in window[:-1]
        if i.after_external_read and i.target_kind == "workdir"
    )
    return internal_queries >= _STAGING_QUERY_THRESHOLD


class MockLLMVerifier:
    """
    Mock Layer 3 verifier — no API key required.

    Receives NormalizedIntent window (not CanonicalizedIntent, since
    MockAnomalyDetector passes NormalizedIntents directly to avoid the
    IntentCanonicalizer dependency in the mock).

    Returns CRITICAL when it sees the data staging pattern.
    """

    async def verify(
        self,
        window: list[NormalizedIntent] | list[CanonicalizedIntent],
        task_signal_hint: str = "",
        policy_name: str = "",
    ) -> AnomalyResult:
        # Works with both NormalizedIntent (mock path) and CanonicalizedIntent (real path)
        # by accessing only fields present on both
        if not window:
            return AnomalyResult(score=_SCORE_LEGIT, cls=AnomalyClass.NORMAL)

        last = window[-1]
        after_ext = any(getattr(i, "after_external_read", False) for i in window)
        last_target = getattr(last, "target_kind", "none")

        if after_ext and last_target in ("external_url", "cloud_metadata"):
            return AnomalyResult(
                score=_SCORE_VERIFIED_CRITICAL,
                cls=AnomalyClass.CRITICAL,
                reasons=("data_staging_detected",),
            )
        return AnomalyResult(score=_SCORE_LEGIT, cls=AnomalyClass.NORMAL)


class MockAnomalyDetector:
    """
    Mock Layer 2 behavioral anomaly scorer — no trained model required.

    Detects the data staging pattern by inspecting the NormalizedIntent window:
      - Intents 1-4: NORMAL (pattern not yet complete)
      - Intent 5 (summarize after 3 broad sweeps): score=0.30 NORMAL
      - Intent 6 (send_teams with external URL): score=0.64 SUSPICIOUS → calls verifier → CRITICAL

    Takes optional gray_zone_verifier; mirrors MLAnomalyDetector's interface
    so it can be swapped in tests without changing governed.py.
    """

    def __init__(self, gray_zone_verifier: LLMVerifier | None = None) -> None:
        self._verifier = gray_zone_verifier

    async def score(
        self,
        window: list[NormalizedIntent],
        task_signal_hint: str = "",
        policy_name: str = "",
    ) -> AnomalyResult:
        if not window:
            return AnomalyResult(score=0.0, cls=AnomalyClass.NORMAL)

        if _is_data_staging(window):
            if self._verifier is not None:
                result = await self._verifier.verify(
                    window,
                    task_signal_hint=task_signal_hint,
                    policy_name=policy_name,
                )
                return result
            return AnomalyResult(
                score=_SCORE_ATTACK_GRAY,
                cls=AnomalyClass.SUSPICIOUS,
                reasons=("data_staging_pattern",),
            )

        # Partial pattern forming (external read seen, queries accumulating)
        external_seen = any(i.after_external_read for i in window)
        if external_seen:
            return AnomalyResult(score=_SCORE_FORMING, cls=AnomalyClass.NORMAL)

        return AnomalyResult(score=_SCORE_LEGIT, cls=AnomalyClass.NORMAL)
