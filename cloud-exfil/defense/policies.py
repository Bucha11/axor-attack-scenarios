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


def research_web_policy() -> ExecutionPolicy:
    """A deliberately permissive research policy: read + outbound fetch allowed.

    The point of this scenario is that containment does NOT come from removing
    the network tool (as in morris2, where send_email was simply absent). Here
    `fetch` is a granted capability — a research agent legitimately browses the
    web. Exfiltration is contained by *taint enforcement*: once the session
    reads a secret it is tainted, and a tainted session may not send to a
    cloud-metadata / private-network destination, even with fetch allowed.
    """
    return ExecutionPolicy(
        name="research_web",
        derived_from=TaskComplexity.MODERATE,
        context_mode=ContextMode.MODERATE,
        compression_mode=CompressionMode.BALANCED,
        child_mode=ChildMode.DENIED,
        max_child_depth=0,
        tool_policy=ToolPolicy(
            allow_read=True,
            allow_write=False,
            allow_bash=False,
            allow_search=True,
            extra_allowed=("fetch",),  # outbound web fetch IS permitted
        ),
        export_mode=ExportMode.SUMMARY,
    )
