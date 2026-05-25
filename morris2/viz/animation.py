# ruff: noqa: I001
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # must precede pyplot import

import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.animation import FuncAnimation  # noqa: E402

_COLOR_CLEAN = "#6B7280"
_COLOR_TAINTED = "#F59E0B"
_COLOR_INFECTED = "#EF4444"
_COLOR_EDGE_NORMAL = "#9CA3AF"
_COLOR_EDGE_BLOCKED = "#EF4444"
_COLOR_EDGE_SAFE = "#10B981"

_NODES = ["Alice", "Bob", "Charlie"]
_EDGES = [("Alice", "Bob"), ("Bob", "Charlie")]
_POS = {"Alice": (0.15, 0.5), "Bob": (0.5, 0.5), "Charlie": (0.85, 0.5)}


def _draw_frame(
    ax: plt.Axes,
    node_colors: dict[str, str],
    edge_colors: dict[tuple[str, str], str],
    blocked_edges: set[tuple[str, str]],
    title: str,
) -> None:
    ax.clear()
    ax.set_xlim(0, 1)
    ax.set_ylim(0.1, 0.9)
    ax.axis("off")
    ax.set_title(title, fontsize=10, fontweight="bold", pad=6)

    # edges
    for src, dst in _EDGES:
        x0, y0 = _POS[src]
        x1, y1 = _POS[dst]
        color = edge_colors.get((src, dst), _COLOR_EDGE_NORMAL)
        ax.annotate(
            "",
            xy=(x1 - 0.07, y1),
            xytext=(x0 + 0.07, y0),
            arrowprops=dict(arrowstyle="->", color=color, lw=1.8),
        )
        if (src, dst) in blocked_edges:
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            ax.text(mx, my + 0.08, "✕ BLOCKED", ha="center", va="center",
                    fontsize=8, color=_COLOR_EDGE_BLOCKED, fontweight="bold")

    # nodes
    for name in _NODES:
        x, y = _POS[name]
        color = node_colors.get(name, _COLOR_CLEAN)
        circle = plt.Circle((x, y), 0.06, color=color, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y - 0.13, name, ha="center", va="top", fontsize=9, fontweight="bold")


def generate_gif(output_path: Path) -> None:
    """
    Generate an 8-frame, two-panel GIF showing Morris II propagation vs containment.

    Frames 0-3: RAW mode — step-by-step infection spreading
    Frames 4-7: GOVERNED mode — taint activates, propagation blocked at step 1
    """
    fig, (ax_raw, ax_gov) = plt.subplots(1, 2, figsize=(10, 3.5))
    fig.patch.set_facecolor("#F9FAFB")

    raw_states = [
        # frame 0 — initial: poison delivered to Alice
        {"nodes": {"Alice": _COLOR_CLEAN, "Bob": _COLOR_CLEAN, "Charlie": _COLOR_CLEAN},
         "edges": {}, "blocked": set(), "label": "Step 0: poisoned email → Alice"},
        # frame 1 — Alice infected, forwards to Bob
        {"nodes": {"Alice": _COLOR_INFECTED, "Bob": _COLOR_CLEAN, "Charlie": _COLOR_CLEAN},
         "edges": {("Alice", "Bob"): _COLOR_EDGE_BLOCKED}, "blocked": set(),
         "label": "Step 1: Alice infected → sends payload to Bob"},
        # frame 2 — Bob infected, forwards to Charlie
        {"nodes": {"Alice": _COLOR_INFECTED, "Bob": _COLOR_INFECTED, "Charlie": _COLOR_CLEAN},
         "edges": {("Alice", "Bob"): _COLOR_INFECTED, ("Bob", "Charlie"): _COLOR_EDGE_BLOCKED},
         "blocked": set(), "label": "Step 2: Bob infected → sends payload to Charlie"},
        # frame 3 — all infected
        {"nodes": {"Alice": _COLOR_INFECTED, "Bob": _COLOR_INFECTED, "Charlie": _COLOR_INFECTED},
         "edges": {("Alice", "Bob"): _COLOR_INFECTED, ("Bob", "Charlie"): _COLOR_INFECTED},
         "blocked": set(), "label": "Step 3: 3/3 agents infected"},
    ]

    gov_states = [
        # frame 4 — initial: poison delivered to Alice
        {"nodes": {"Alice": _COLOR_CLEAN, "Bob": _COLOR_CLEAN, "Charlie": _COLOR_CLEAN},
         "edges": {}, "blocked": set(), "label": "Step 0: poisoned email → Alice"},
        # frame 5 — Alice reads email (tainted), tries to send — BLOCKED
        {"nodes": {"Alice": _COLOR_TAINTED, "Bob": _COLOR_CLEAN, "Charlie": _COLOR_CLEAN},
         "edges": {("Alice", "Bob"): _COLOR_EDGE_BLOCKED},
         "blocked": {("Alice", "Bob")},
         "label": "Step 1: taint active → send_email DENIED (Layer 1)"},
        # frame 6 — chain dead, Bob/Charlie clean
        {"nodes": {"Alice": _COLOR_TAINTED, "Bob": _COLOR_CLEAN, "Charlie": _COLOR_CLEAN},
         "edges": {("Alice", "Bob"): _COLOR_EDGE_SAFE, ("Bob", "Charlie"): _COLOR_EDGE_SAFE},
         "blocked": set(), "label": "Step 2: 0/3 agents infected — chain dead"},
        # frame 7 — final state
        {"nodes": {"Alice": _COLOR_TAINTED, "Bob": _COLOR_CLEAN, "Charlie": _COLOR_CLEAN},
         "edges": {("Alice", "Bob"): _COLOR_EDGE_SAFE, ("Bob", "Charlie"): _COLOR_EDGE_SAFE},
         "blocked": set(), "label": "Contained: export=RESTRICTED + Layer 1 denial"},
    ]

    def animate(frame: int) -> None:
        _draw_frame(ax_raw, raw_states[frame if frame < 4 else 3]["nodes"],
                    raw_states[frame if frame < 4 else 3]["edges"],
                    raw_states[frame if frame < 4 else 3]["blocked"],
                    f"RAW — {raw_states[frame if frame < 4 else 3]['label']}")

        _draw_frame(ax_gov, gov_states[frame - 4 if frame >= 4 else 0]["nodes"],
                    gov_states[frame - 4 if frame >= 4 else 0]["edges"],
                    gov_states[frame - 4 if frame >= 4 else 0]["blocked"],
                    f"GOVERNED (Axor) — {gov_states[frame - 4 if frame >= 4 else 0]['label']}")

        # legend
        legend_elements = [
            mpatches.Patch(color=_COLOR_CLEAN, label="Clean"),
            mpatches.Patch(color=_COLOR_TAINTED, label="Tainted"),
            mpatches.Patch(color=_COLOR_INFECTED, label="Infected"),
        ]
        fig.legend(handles=legend_elements, loc="lower center", ncol=3,
                   fontsize=8, framealpha=0.8)

    anim = FuncAnimation(fig, animate, frames=8, interval=1200, repeat=True)
    anim.save(str(output_path), writer="pillow", fps=1)
    plt.close(fig)


if __name__ == "__main__":
    out = Path("morris2_demo.gif")
    generate_gif(out)
    print(f"Saved {out}")
