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


def email_sandboxed() -> ExecutionPolicy:
    """
    Governed policy for email agents.

    read_email auto-allowed via read_* prefix rule in CapabilityResolver.
    send_email has no known prefix and is not in extra_allowed → Layer 1 denies it.
    ExportMode.RESTRICTED ensures nothing propagates out of the node.
    """
    return ExecutionPolicy(
        name="email_sandboxed",
        derived_from=TaskComplexity.FOCUSED,
        context_mode=ContextMode.MINIMAL,
        compression_mode=CompressionMode.AGGRESSIVE,
        child_mode=ChildMode.DENIED,
        max_child_depth=0,
        tool_policy=ToolPolicy(
            allow_read=True,
            allow_write=False,
            allow_bash=False,
            allow_search=False,
            extra_allowed=("read_email",),
            # send_email omitted → not in capabilities → Layer 1 denies it
        ),
        export_mode=ExportMode.RESTRICTED,
    )
