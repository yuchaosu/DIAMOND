#!/usr/bin/env python3.11
"""Throughput of the hardware methods (QuTiP/CPU excluded) over all provenance matrices, q14-20.

Dot per (method, workload) that has a result; x = throughput (MAC/cycle, log); colored by matrix class.
Peak = 256 MAC/cyc (16x16 array). Source: result/throughput_q14-20.csv.
DIAMOND on banded/fill-in sits at the 256 peak by construction (useful-MAC derived as compute*256);
its diagonal points (~56) are the non-circular, bandwidth-bound numbers."""
import csv, os
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

REPO = "/home/ysu34/DIAMOND/diamond"
SRC = os.path.join(REPO, "result", "throughput_q14-20.csv")
METHODS = [("DIAMOND", "DIAMOND_MACpc", 3), ("Trapezoid-HS", "Trapezoid_MACpc", 2),
           ("Flexagon", "Flexagon_MACpc", 1), ("TPU", "TPU_MACpc", 0)]
# class -> color (single-diagonal folds into diagonal)
CLSCOL = {"diagonal": "#0072B2", "single-diagonal": "#0072B2", "banded": "#E69F00",
          "fill-in": "#CC79A7", "special": "#5a5a5a"}
CLS_LEGEND = [("diagonal", "#0072B2"), ("banded", "#E69F00"), ("fill-in", "#CC79A7"), ("special", "#5a5a5a")]
INK, MUTED, GRID = "#1a1a1a", "#5a5a5a", "#dcdcdc"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": MUTED,
                     "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})

rows = list(csv.DictReader(open(SRC)))
fig, ax = plt.subplots(1, 1, figsize=(9.2, 4.6))
for name, col, y in METHODS:
    pts = [(float(r[col]), r["class"]) for r in rows if r[col]]
    for i, (v, cls) in enumerate(sorted(pts)):
        jit = ((i % 7) - 3) / 3.0 * 0.26                    # deterministic vertical spread
        ax.scatter(v, y + jit, s=46, color=CLSCOL.get(cls, MUTED), edgecolor="white",
                   linewidth=0.8, alpha=0.9, zorder=3)

ax.axvline(256, color=INK, ls="--", lw=1.1, zorder=2)
ax.text(256, 3.62, " peak 256", va="bottom", ha="center", fontsize=8.5, color=INK, fontweight="bold")
ax.set_xscale("log"); ax.set_xlim(1e-10, 1e3)
ax.set_yticks([m[2] for m in METHODS]); ax.set_yticklabels([m[0] for m in METHODS], fontsize=11)
ax.set_ylim(-0.6, 3.9)
ax.set_xlabel("throughput   (MAC / cycle, log)", fontsize=11)
ax.set_title("Hardware throughput across all matrices  (q=14–20, 16×16)",
             fontsize=12.5, fontweight="bold", loc="center", pad=10)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0); ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
ax.legend(handles=[Line2D([0], [0], marker="o", ls="", mfc=c, mec="white", ms=8, label=cls)
                   for cls, c in CLS_LEGEND],
          loc="upper center", frameon=False, fontsize=9.5, ncol=4, bbox_to_anchor=(0.5, -0.14))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diamond_throughput")
fig.savefig(OUT + ".png", dpi=200, bbox_inches="tight", facecolor="white")
fig.savefig(OUT + ".pdf", bbox_inches="tight", facecolor="white")
print("wrote", OUT + ".{png,pdf}")
