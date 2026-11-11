#!/usr/bin/env python3.11
"""Two-panel figure: (A) matrix-pattern comparison (diagonal/banded/fill-in) — compute vs memory,
showing the memory-bound -> compute-bound transition; (B) l1/l2/l3 ablation per pattern.
Measured from outputs/diamond at 16x16 (256 PE), q=14. PE clock 700 MHz (time = cyc/0.7)."""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

F_GHZ = 0.700
cyc_ns = lambda c: c / F_GHZ
us = lambda ns: ns / 1000.0
mem_ns = lambda mib: mib * 1024 * 1024 / 2048.0

# measured (l3) for pattern comparison: compute cyc, HBM MiB
PAT = [  # label, compute_cyc, hbm_mib, color-note
    ("Diagonal\n(tfim)",  408,     3.25),
    ("Banded\n(qmaxcut)", 310068,  528.33),
    ("Fill-in\n(bh)",     3716200, 3092.15),
]
# ablation compute cycles: l1, l2, l3  (None = did not finish)
ABL = [
    ("Diagonal\n(tfim)",  [65536,    65536,    408]),
    ("Banded\n(qmaxcut)", [28253550, 3998720,  310068]),
    ("Fill-in\n(bh)",     [None,     17207059, 3716200]),
]

C_COMPUTE, C_MEM = "#0072B2", "#009E73"
L_COL = ["#c6dbef", "#6baed6", "#08519c"]   # l1,l2,l3 sequential blue
INK, MUTED, GRID = "#1a1a1a", "#5a5a5a", "#dddddd"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": MUTED,
                     "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})

fig, (axA, axB) = plt.subplots(1, 2, figsize=(12.6, 4.6), gridspec_kw={"wspace": 0.32})

# ===== Panel A: compute vs memory per pattern (log time) =====
yb = np.arange(len(PAT))[::-1]
bh = 0.34
for i, (lab, ccyc, mib) in enumerate(PAT):
    y = yb[i]
    ct, mt = us(cyc_ns(ccyc)), us(mem_ns(mib))
    mk = max(ct, mt)
    axA.barh(y + bh/1.9, ct, height=bh, color=C_COMPUTE, edgecolor="white", linewidth=1.2, zorder=3)
    axA.barh(y - bh/1.9, mt, height=bh, color=C_MEM, edgecolor="white", linewidth=1.2, zorder=3)
    bound = "compute-bound" if ct >= mt else "memory-bound"
    lbl = f"makespan {mk*1000:.0f} ns" if mk < 1 else (f"makespan {mk:.0f} µs" if mk < 1000 else f"makespan {mk/1000:.1f} ms")
    axA.text(mk * 1.25, y, lbl + f"\n({bound})", va="center", ha="left",
             fontsize=8.6, color=INK, fontweight="bold")
    axA.text(-0.02, y, lab, transform=axA.get_yaxis_transform(), va="center", ha="right", fontsize=9.5)
axA.set_xscale("log")
axA.set_xlim(0.3, 3e5)
axA.set_ylim(-0.7, len(PAT) - 0.3)
axA.set_yticks([])
axA.set_xlabel("time  (µs, log)", fontsize=10)
axA.set_title("A.  Pattern → profile: memory-bound → compute-bound",
              fontsize=11.5, fontweight="bold", loc="left", pad=10)
axA.legend(handles=[Patch(fc=C_COMPUTE, label="compute"), Patch(fc=C_MEM, label="memory (HBM)")],
           loc="lower right", frameon=False, fontsize=9)
for s in ("top", "right", "left"): axA.spines[s].set_visible(False)
axA.grid(axis="x", color=GRID, lw=0.6); axA.set_axisbelow(True); axA.tick_params(axis="y", length=0)

# ===== Panel B: l1/l2/l3 ablation (compute cycles, log) =====
x = np.arange(len(ABL)); w = 0.26
for j, lvl in enumerate(["l1", "l2", "l3"]):
    vals = [a[1][j] for a in ABL]
    xs = x + (j - 1) * w
    plotted = [(xi, v) for xi, v in zip(xs, vals) if v is not None]
    axB.bar([p[0] for p in plotted], [p[1] for p in plotted], width=w, color=L_COL[j],
            edgecolor="white", linewidth=1.0, label=lvl, zorder=3)
    for xi, v in zip(xs, vals):
        if v is None:
            axB.text(xi, 6e4, "DNF", rotation=90, va="bottom", ha="center", fontsize=8, color=MUTED)
axB.set_yscale("log")
axB.set_ylim(2e2, 1e8)
axB.set_xticks(x); axB.set_xticklabels([a[0] for a in ABL], fontsize=9.5)
axB.set_ylabel("compute cycles  (log)", fontsize=10)
axB.set_title("B.  Ablation: zeroskip (l1→l2) + cbalance (l2→l3)", fontsize=11.5, fontweight="bold", loc="left", pad=10)
axB.legend(frameon=False, fontsize=9, ncol=3, loc="upper right")
# reduction annotations
for xi, a in zip(x, ABL):
    v = a[1]
    if v[0] and v[2]:
        axB.annotate(f"{v[0]/v[2]:.0f}×", (xi, v[2]), (xi, v[2]*0.35), ha="center", fontsize=8.5,
                     color=INK, fontweight="bold")
for s in ("top", "right"): axB.spines[s].set_visible(False)
axB.grid(axis="y", color=GRID, lw=0.6); axB.set_axisbelow(True)

fig.suptitle("DIAMOND per-pattern breakdown & ablation — q=14, 16×16 (256 PE)",
             fontsize=13, fontweight="bold", x=0.015, ha="left", y=1.00)
fig.text(0.015, -0.02, "Measured from outputs/diamond. cbalance drives the biggest cut on diagonal (spreads the one long "
         "diagonal across 256 PEs); zeroskip helps only where zeros exist. fill-in l1 did not finish (DNF).",
         fontsize=8, color=MUTED)
fig.savefig("/tmp/claude-435053/pattern_ablation.png", dpi=200, bbox_inches="tight", facecolor="white")
fig.savefig("/tmp/claude-435053/pattern_ablation.pdf", bbox_inches="tight", facecolor="white")
print("saved. makespans µs:",
      {p[0].split(chr(10))[0]: round(us(max(cyc_ns(p[1]), mem_ns(p[2]))), 2) for p in PAT})
