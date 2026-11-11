#!/usr/bin/env python3.11
"""Plot the RECORDED global-cycle Gantt from gantt_sim.py's timeline_*.csv (one shared cycle clock).

Pure plotter: every bar is placed at its recorded (start_cyc, end_cyc); no scheduling here.
x-axis = global cycle (real, absolute). Each pattern on its own scale (they span 1e3..1e7 cycles)."""
import csv, os
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
PANELS = [("timeline_tfim_14.csv", "Diagonal  (tfim, D=1)"),
          ("timeline_qmaxcut_14.csv", "Banded  (qmaxcut)"),
          ("timeline_bh_14.csv", "Fill-in  (bh)")]
STAGES = [("Memory", "#009E73"), ("Compute", "#0072B2"), ("Route", "#E69F00"), ("Accumulate", "#CC79A7")]
YROW = {"Memory": 3, "Compute": 2, "Route": 1, "Accumulate": 0}
COL = {s: c for s, c in STAGES}
INK, MUTED, GRID = "#1a1a1a", "#5a5a5a", "#dcdcdc"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": MUTED,
                     "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})


def load(fname):
    rows = []
    for r in csv.DictReader(open(os.path.join(HERE, fname))):
        rows.append((r["stage"], float(r["start_cyc"]), float(r["end_cyc"])))
    return rows


def fmt_cyc(v):
    if v >= 1e6:
        return f"{v/1e6:.1f}M"
    if v >= 1e3:
        return f"{v/1e3:.0f}k"
    return f"{v:.0f}"


panels = [(f, t) for f, t in PANELS if os.path.exists(os.path.join(HERE, f))]
fig, axes = plt.subplots(len(panels), 1, figsize=(9.6, 2.15 * len(panels)))
if len(panels) == 1:
    axes = [axes]

for ax, (fname, title) in zip(axes, panels):
    rows = load(fname)
    makespan = max(e for _, _, e in rows)
    for stage, st, en in rows:
        ax.barh(YROW[stage], en - st, left=st, height=0.6, color=COL[stage], edgecolor="white",
                linewidth=0.9, zorder=3)
    ax.set_yticks([YROW[s] for s, _ in STAGES]); ax.set_yticklabels([s for s, _ in STAGES], fontsize=9)
    ax.set_ylim(-0.7, 3.7); ax.set_xlim(0, makespan * 1.02)
    ax.set_title(title, fontsize=10.5, fontweight="bold", loc="left", pad=5, color=INK)
    ax.set_xticks([])                                        # x-axis removed
    for sp in ("top", "right", "left", "bottom"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="both", length=0)

    # zoom inset (upper-right, in-panel); a rectangle marks the [0,ZOOM] source region at the start
    if makespan > 5000:
        ZOOM = 230
        axin = ax.inset_axes([0.60, 0.50, 0.37, 0.47], transform=ax.transAxes)
        for stage, st, en in rows:
            axin.barh(YROW[stage], en - st, left=st, height=0.62, color=COL[stage], edgecolor="white",
                      linewidth=0.9, zorder=3)
        axin.set_xlim(0, ZOOM); axin.set_ylim(-0.7, 3.7)
        axin.set_yticks([]); axin.set_xticks([])
        axin.set_facecolor("white")
        for sp in axin.spines.values():
            sp.set_visible(True); sp.set_color(MUTED); sp.set_linewidth(0.9)
        # rectangle on the main panel marking the zoomed [0,ZOOM] region + connectors to the inset
        rect, conns = ax.indicate_inset_zoom(axin, edgecolor=INK, lw=1.3, alpha=0.9)
        for c in conns:
            c.set_color(MUTED); c.set_linewidth(0.8); c.set_alpha(0.55)

fig.legend(handles=[Patch(fc=c, label=s) for s, c in STAGES],
           loc="lower center", frameon=False, fontsize=9.5, ncol=4, bbox_to_anchor=(0.5, -0.01))
fig.tight_layout(rect=[0, 0.04, 1, 1.0])
OUT = os.path.join(HERE, "gantt_real_q14")
fig.savefig(OUT + ".png", dpi=200, bbox_inches="tight", facecolor="white")
fig.savefig(OUT + ".pdf", bbox_inches="tight", facecolor="white")
print("wrote", OUT + ".{png,pdf}")
