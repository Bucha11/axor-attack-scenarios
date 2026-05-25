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
_COLOR_QUERIED_PASS = "#3B82F6"
_COLOR_GRAY_ZONE = "#F97316"
_COLOR_CRITICAL = "#8B5CF6"
_COLOR_BLOCKED = "#EF4444"
_COLOR_EDGE_NORMAL = "#9CA3AF"
_COLOR_EDGE_BLOCKED = "#EF4444"
_COLOR_EDGE_PASS = "#10B981"

# Node layout: Email(attacker), SP, OD, Teams, Proxy(external)
_NODES = {
    "Email": (0.12, 0.7),
    "SharePoint": (0.35, 0.85),
    "OneDrive": (0.35, 0.5),
    "Teams": (0.35, 0.15),
    "Copilot": (0.62, 0.5),
    "Proxy": (0.88, 0.5),
}
_EDGES = [
    ("Email", "Copilot"),
    ("Copilot", "SharePoint"),
    ("Copilot", "OneDrive"),
    ("Copilot", "Teams"),
    ("Copilot", "Proxy"),
]


def _draw_frame(
    ax: plt.Axes,
    node_colors: dict[str, str],
    active_edges: dict[tuple[str, str], str],
    blocked_edges: set[tuple[str, str]],
    annotations: dict[str, str],
    title: str,
) -> None:
    ax.clear()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title(title, fontsize=9, fontweight="bold", pad=4)

    for src, dst in _EDGES:
        x0, y0 = _NODES[src]
        x1, y1 = _NODES[dst]
        color = active_edges.get((src, dst), _COLOR_EDGE_NORMAL)
        ax.annotate(
            "",
            xy=(x1 - 0.07, y1),
            xytext=(x0 + 0.07, y0),
            arrowprops=dict(arrowstyle="->", color=color, lw=1.6),
        )
        if (src, dst) in blocked_edges:
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            ax.text(mx, my + 0.06, "✕", ha="center", va="center",
                    fontsize=12, color=_COLOR_BLOCKED, fontweight="bold")

    for name, (x, y) in _NODES.items():
        color = node_colors.get(name, _COLOR_CLEAN)
        circle = plt.Circle((x, y), 0.055, color=color, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y - 0.11, name, ha="center", va="top", fontsize=7.5, fontweight="bold")
        if name in annotations:
            ax.text(x, y + 0.10, annotations[name], ha="center", va="bottom",
                    fontsize=6.5, color=color, style="italic")


def generate_gif(output_path: Path) -> None:
    """
    Generate 8-frame two-panel GIF: RAW exfiltration vs GOVERNED containment.

    Frames 0-3: RAW — step-by-step queries turn red, data flows to Proxy
    Frames 4-7: GOVERNED — taint yellow, queries blue (Layer 1 pass),
                send_teams triggers orange (Layer 2) then purple (Layer 3) then BLOCKED
    """
    fig, (ax_raw, ax_gov) = plt.subplots(1, 2, figsize=(11, 4))
    fig.patch.set_facecolor("#F9FAFB")

    raw_frames = [
        {
            "nodes": {n: _COLOR_CLEAN for n in _NODES},
            "edges": {},
            "blocked": set(),
            "ann": {},
            "label": "Step 0: hidden email → Copilot",
        },
        {
            "nodes": {"Email": _COLOR_BLOCKED, "Copilot": _COLOR_TAINTED,
                      "SharePoint": _COLOR_BLOCKED, **{n: _COLOR_CLEAN for n in ["OneDrive", "Teams", "Proxy"]}},
            "edges": {("Email", "Copilot"): _COLOR_BLOCKED, ("Copilot", "SharePoint"): _COLOR_BLOCKED},
            "blocked": set(),
            "ann": {"SharePoint": "847 docs"},
            "label": "Step 1: Copilot → SharePoint (847 docs)",
        },
        {
            "nodes": {"Email": _COLOR_BLOCKED, "Copilot": _COLOR_TAINTED,
                      "SharePoint": _COLOR_BLOCKED, "OneDrive": _COLOR_BLOCKED,
                      "Teams": _COLOR_BLOCKED, "Proxy": _COLOR_CLEAN},
            "edges": {("Copilot", "SharePoint"): _COLOR_BLOCKED,
                      ("Copilot", "OneDrive"): _COLOR_BLOCKED,
                      ("Copilot", "Teams"): _COLOR_BLOCKED},
            "blocked": set(),
            "ann": {"OneDrive": "234 docs", "Teams": "156 convos"},
            "label": "Step 2: +OneDrive +Teams (1,237 total)",
        },
        {
            "nodes": {n: _COLOR_BLOCKED for n in _NODES},
            "edges": {e: _COLOR_BLOCKED for e in _EDGES},
            "blocked": set(),
            "ann": {"Proxy": "1,237 docs"},
            "label": "EXFILTRATED: 1,237 docs. 0 alerts.",
        },
    ]

    gov_frames = [
        {
            "nodes": {n: _COLOR_CLEAN for n in _NODES},
            "edges": {},
            "blocked": set(),
            "ann": {},
            "label": "Step 0: hidden email → Copilot",
        },
        {
            "nodes": {"Email": _COLOR_TAINTED, "Copilot": _COLOR_TAINTED,
                      "SharePoint": _COLOR_QUERIED_PASS,
                      **{n: _COLOR_CLEAN for n in ["OneDrive", "Teams", "Proxy"]}},
            "edges": {("Email", "Copilot"): _COLOR_TAINTED,
                      ("Copilot", "SharePoint"): _COLOR_QUERIED_PASS},
            "blocked": set(),
            "ann": {"Copilot": "taint: ON", "SharePoint": "Layer 1: PASS"},
            "label": "Step 1: taint active — Layer 1 passes queries",
        },
        {
            "nodes": {"Email": _COLOR_TAINTED, "Copilot": _COLOR_TAINTED,
                      "SharePoint": _COLOR_QUERIED_PASS, "OneDrive": _COLOR_QUERIED_PASS,
                      "Teams": _COLOR_QUERIED_PASS, "Proxy": _COLOR_CLEAN},
            "edges": {("Copilot", "SharePoint"): _COLOR_QUERIED_PASS,
                      ("Copilot", "OneDrive"): _COLOR_QUERIED_PASS,
                      ("Copilot", "Teams"): _COLOR_QUERIED_PASS},
            "blocked": set(),
            "ann": {"Copilot": "Layer 2: 0.64 ⚠"},
            "label": "Step 2: Layer 2 gray zone (score=0.64)",
        },
        {
            "nodes": {"Email": _COLOR_TAINTED, "Copilot": _COLOR_CRITICAL,
                      "SharePoint": _COLOR_QUERIED_PASS, "OneDrive": _COLOR_QUERIED_PASS,
                      "Teams": _COLOR_QUERIED_PASS, "Proxy": _COLOR_CLEAN},
            "edges": {("Copilot", "Proxy"): _COLOR_BLOCKED},
            "blocked": {("Copilot", "Proxy")},
            "ann": {"Copilot": "Layer 3: CRITICAL", "Proxy": "BLOCKED"},
            "label": "Layer 3: data staging detected → BLOCKED",
        },
    ]

    def animate(frame: int) -> None:
        fi = frame if frame < 4 else frame - 4
        raw_s = raw_frames[fi]
        gov_s = gov_frames[fi]

        _draw_frame(ax_raw, raw_s["nodes"], raw_s["edges"], raw_s["blocked"],
                    raw_s["ann"], f"RAW — {raw_s['label']}")
        _draw_frame(ax_gov, gov_s["nodes"], gov_s["edges"], gov_s["blocked"],
                    gov_s["ann"], f"GOVERNED (Axor) — {gov_s['label']}")

        if frame == 7:
            fig.text(0.5, 0.01,
                     "Every action was legitimate. The chain was not.",
                     ha="center", fontsize=9, style="italic", color="#374151")

        legend_elements = [
            mpatches.Patch(color=_COLOR_CLEAN, label="Clean"),
            mpatches.Patch(color=_COLOR_TAINTED, label="Tainted"),
            mpatches.Patch(color=_COLOR_QUERIED_PASS, label="Queried (pass)"),
            mpatches.Patch(color=_COLOR_GRAY_ZONE, label="Layer 2 gray zone"),
            mpatches.Patch(color=_COLOR_CRITICAL, label="Layer 3 critical"),
            mpatches.Patch(color=_COLOR_BLOCKED, label="Blocked/Infected"),
        ]
        fig.legend(handles=legend_elements, loc="upper center", ncol=6,
                   fontsize=7, framealpha=0.9, bbox_to_anchor=(0.5, 0.0))

    anim = FuncAnimation(fig, animate, frames=8, interval=1200, repeat=True)
    anim.save(str(output_path), writer="pillow", fps=1)
    plt.close(fig)


if __name__ == "__main__":
    out = Path("copilot_staging_demo.gif")
    generate_gif(out)
    print(f"Saved {out}")
