#!/usr/bin/env python3.11
"""Figure 1: matrix-pattern comparison (diagonal/banded/fill-in) — compute vs memory,
showing the memory-bound -> compute-bound transition. Measured from outputs/diamond,
16x16 (256 PE), q=14, l3. PE clock 700 MHz (time = cyc/0.7)."""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

F_GHZ = 0.700
cyc_ns = lambda c: c / F_GHZ
us = lambda ns: ns / 1000.0
mem_ns = lambda mib: mib * 1024 * 1024 / 2048.0

PAT = [("Diagonal\n(tfim)", 408, 3.25), ("Banded\n(qmaxcut)", 310068, 528.33), ("Fill-in\n(bh)", 3716200, 3092.15)]
C_COMPUTE, C_MEM = "#0072B2", "#009E73"
INK, MUTED, GRID = "#1a1a1a", "#5a5a5a", "#dddddd"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": MUTED,
                     "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})

fig, axA = plt.subplots(1, 1, figsize=(7.4, 3.9))
yb = np.arange(len(PAT))[::-1]; bh = 0.34
for i, (lab, ccyc, mib) in enumerate(PAT):
    y = yb[i]; ct, mt = us(cyc_ns(ccyc)), us(mem_ns(mib)); mk = max(ct, mt)
    axA.barh(y + bh/1.9, ct, height=bh, color=C_COMPUTE, edgecolor="white", linewidth=1.2, zorder=3)
    axA.barh(y - bh/1.9, mt, height=bh, color=C_MEM, edgecolor="white", linewidth=1.2, zorder=3)
    bound = "compute-bound" if ct >= mt else "memory-bound"
    lbl = f"{mk*1000:.0f} ns" if mk < 1 else (f"{mk:.0f} µs" if mk < 1000 else f"{mk/1000:.1f} ms")
    axA.text(mk * 1.28, y, f"makespan {lbl}\n({bound})", va="center", ha="left", fontsize=9, color=INK, fontweight="bold")
    axA.text(-0.02, y, lab, transform=axA.get_yaxis_transform(), va="center", ha="right", fontsize=10)
axA.set_xscale("log"); axA.set_xlim(0.3, 3e5); axA.set_ylim(-0.7, len(PAT) - 0.3); axA.set_yticks([])
axA.set_xlabel("time  (µs, log)", fontsize=10)
axA.set_title("Matrix pattern → profile: memory-bound → compute-bound  (q=14, 16×16)",
              fontsize=11.5, fontweight="bold", loc="left", pad=10)
axA.legend(handles=[Patch(fc=C_COMPUTE, label="compute"), Patch(fc=C_MEM, label="memory (HBM)")],
           loc="lower right", frameon=False, fontsize=9)
for s in ("top", "right", "left"): axA.spines[s].set_visible(False)
axA.grid(axis="x", color=GRID, lw=0.6); axA.set_axisbelow(True); axA.tick_params(axis="y", length=0)
fig.text(0.01, -0.02, "Measured from outputs/diamond (l3). As D grows (1→27→143), the bottleneck flips from HBM to the MAC array.",
         fontsize=8, color=MUTED)
fig.savefig("/tmp/claude-435053/diamond_pattern.png", dpi=200, bbox_inches="tight", facecolor="white")
fig.savefig("/tmp/claude-435053/diamond_pattern.pdf", bbox_inches="tight", facecolor="white")
print("pattern figure saved")
