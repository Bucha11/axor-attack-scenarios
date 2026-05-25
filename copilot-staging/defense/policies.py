from __future__ import annotations

from axor_core.contracts.policy import (
    ChildMode,
    CompressionMode,
    ContextMode,
    ExecutionPolicy,
    ExportMode,
    TaskComplexity,
    ToolPolicy,
)

_ALLOWED_TOOLS = (
    "web_fetch",
    "query_sharepoint",
    "query_onedrive",
    "query_teams",
    "summarize",
    "send_teams",
)


def copilot_standard() -> ExecutionPolicy:
    """
    Realistic Microsoft Copilot-style policy.

    All 6 corporate tools are allowed. ExportMode.FULL — the agent CAN
    legitimately send via Teams. Layer 1 is intentionally blind to the
    data staging pattern. Only Layer 2/3 behavioral analysis catches it.
    """
    return ExecutionPolicy(
        name="copilot_standard",
        derived_from=TaskComplexity.MODERATE,
        context_mode=ContextMode.MODERATE,
        compression_mode=CompressionMode.BALANCED,
        child_mode=ChildMode.DENIED,
        max_child_depth=0,
        tool_policy=ToolPolicy(
            allow_read=False,
            allow_write=False,
            allow_bash=False,
            allow_search=False,
            extra_allowed=_ALLOWED_TOOLS,
        ),
        export_mode=ExportMode.FULL,
    )
