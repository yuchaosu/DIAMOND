#!/usr/bin/env python3.11
"""H^k occupancy — share of the whole operator build (U = sum c_k H^k) spent on the sparse
matrix-products H^k vs the Taylor accumulation. Measured on QuTiP 5 CSR (CPU), q=14..20.
occupancy = t_prod / t_full  (t_prod = SpMSpM chain; t_full = products + accumulation).
100% stacked bars, grouped by matrix pattern; the H^k share is the emphasized segment.
Data EMBEDDED below (measured; source: result/dia_csr_transfer_q14-20.csv, rows with time:ok)."""
import os
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ORDER = ["diagonal", "banded", "fill-in"]

# ---- EMBEDDED measured data: (class, q, family, hk_occupancy = t_prod/t_full) ----
ROWS = [
    ("diagonal", 14, "tfim", 0.4938),
    ("diagonal", 16, "tfim", 0.4715),
    ("diagonal", 18, "tfim", 0.5197),
    ("diagonal", 20, "tfim", 0.4770),
    ("banded",   14, "qmaxcut", 0.5043),
    ("banded",   16, "qmaxcut", 0.6161),
    ("banded",   18, "qmaxcut", 0.6592),
    ("fill-in",  14, "bh", 0.6576),
    ("fill-in",  16, "bh", 0.6895),
]
rows = sorted(ROWS, key=lambda x: (ORDER.index(x[0]), x[1]))

C_HK, C_ACC = "#0072B2", "#c7c7c7"      # H^k products (compute-blue) vs accumulation (muted)
INK, MUTED, GRID = "#1a1a1a", "#5a5a5a", "#dcdcdc"
CLS_C = {"diagonal": "#2b8cbe", "banded": "#E69F00", "fill-in": "#CC79A7"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10.5, "axes.edgecolor": MUTED,
                     "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})

fig, ax = plt.subplots(1, 1, figsize=(9.0, 4.6))
y = list(range(len(rows)))[::-1]                       # top-to-bottom in sorted order
for yy, (cls, q, fam, occ) in zip(y, rows):
    ax.barh(yy, occ, height=0.66, color=C_HK, edgecolor="white", linewidth=1.4, zorder=3)
    ax.barh(yy, 1 - occ, left=occ, height=0.66, color=C_ACC, edgecolor="white", linewidth=1.4, zorder=3)
    ax.text(occ - 0.012, yy, f"{occ*100:.0f}%", va="center", ha="right", fontsize=9.5,
            fontweight="bold", color="white", zorder=4)
    ax.text(-0.015, yy, f"{fam}  q{q}", va="center", ha="right", fontsize=9.6, color=INK)
    ax.text(-0.145, yy, "", va="center", ha="right")   # spacer for group tag drawn below

# pattern group brackets on the far left
seen = {}
for yy, (cls, *_1) in zip(y, rows):
    seen.setdefault(cls, []).append(yy)
for cls, ys in seen.items():
    ax.text(-0.235, sum(ys) / len(ys), cls, va="center", ha="center", rotation=90,
            fontsize=10, fontweight="bold", color=CLS_C[cls])
    ax.plot([-0.205, -0.205], [min(ys) - 0.34, max(ys) + 0.34], color=CLS_C[cls], lw=2.4,
            solid_capstyle="round", clip_on=False, zorder=5)

ax.axvline(0.5, color=MUTED, ls=":", lw=1.0, zorder=2)
ax.set_xlim(0, 1.0); ax.set_ylim(-0.7, len(rows) - 0.3)
ax.set_yticks([]); ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_xticklabels(["0", "25%", "50%", "75%", "100%"])
ax.set_xlabel("share of the operator build", fontsize=10.5)
ax.set_title("H$^k$ occupancy", fontsize=12.5, fontweight="bold", loc="center", pad=10)
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0); ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
ax.legend(handles=[Patch(fc=C_HK, label="H$^k$ products (SpMSpM)"),
                   Patch(fc=C_ACC, label="Taylor accumulation")],
          loc="upper center", frameon=False, fontsize=9.5, ncol=2, bbox_to_anchor=(0.5, -0.13))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diamond_occupancy")
fig.savefig(OUT + ".png", dpi=200, bbox_inches="tight", facecolor="white")
fig.savefig(OUT + ".pdf", bbox_inches="tight", facecolor="white")
print("wrote", OUT + ".{png,pdf}  rows:", len(rows))
