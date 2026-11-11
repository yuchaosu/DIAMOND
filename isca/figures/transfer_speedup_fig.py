#!/usr/bin/env python3.11
"""Combined: data transfer (bars) + DIAMOND speedup over QuTiP (line), q=14, three patterns.

Bars (left, log): memory transferred to build the operator, CSR vs CSD (both store only true nnz;
  differ only in the pointer array — CSR keys by row (n), CSD by diagonal (D)):  8*nnz + 4*{n | D},
  summed over the chained build with DIAMOND's non-fused HBM event model.
Line (right):     DIAMOND speedup = QuTiP whole-build time (t_full) / DIAMOND makespan,
  makespan = max(compute, memory);  compute = compute_mac cyc @700MHz, memory = HBM bytes / 2048.

Data is EMBEDDED below (measured q=14).  Provenance per pattern:
  diagonal (tfim_14_4):   qutip t_full 0.001387 s ; DIAMOND compute 0.583 us, mem 1.664 us -> makespan 1.664 us
  banded   (qmaxcut_14_4): qutip t_full 1.016878 s ; DIAMOND compute 442.954 us, mem 270.504 us -> makespan 442.954 us
  fill-in  (bh_14_5):     qutip t_full 9.979542 s ; DIAMOND compute 13132.003 us, mem 3181.547 us -> makespan 13132.003 us
  Sources: result/dia_csr_transfer_q14-20.csv (nnz_seq/D_seq/qutip_t_full), isca/figures/gantt_data/{pat}_14.csv.
"""
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# ---- EMBEDDED measured data (q=14) ----
LABELS  = ["Diagonal\n(tfim)", "Banded\n(qmaxcut)", "Fill-in\n(bh)"]
CSR_MiB = [2.4375, 269.8516, 3113.6798]        # 8*nnz + 4*nrows(=n), summed over the build
CSD_MiB = [1.6250, 269.1537, 3113.5221]        # 8*nnz + 4*D
SPEEDUP = [833.5,  2295.7,   759.9]            # QuTiP t_full / DIAMOND makespan

C_CSR, C_CSD, C_SPD = "#6baed6", "#08519c", "#D55E00"
INK, MUTED, GRID = "#1a1a1a", "#5a5a5a", "#dcdcdc"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": MUTED,
                     "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})

fig, axL = plt.subplots(1, 1, figsize=(8.2, 4.9))
x = np.arange(len(LABELS)); w = 0.34
axL.bar(x - w / 2, CSR_MiB, width=w, color=C_CSR, edgecolor="white", linewidth=1.2, zorder=3, label="CSR transfer")
axL.bar(x + w / 2, CSD_MiB, width=w, color=C_CSD, edgecolor="white", linewidth=1.2, zorder=3, label="CSD transfer")
for xi, (c, d) in enumerate(zip(CSR_MiB, CSD_MiB)):
    axL.text(xi - w / 2, c * 1.15, f"{c:.0f}" if c >= 10 else f"{c:.1f}", ha="center", va="bottom", fontsize=8, color=MUTED)
    axL.text(xi + w / 2, d * 1.15, f"{d:.0f}" if d >= 10 else f"{d:.1f}", ha="center", va="bottom", fontsize=8, color=C_CSD, fontweight="bold")
axL.set_yscale("log"); axL.set_ylim(0.6, 2e4)
axL.set_ylabel("memory transferred  (MiB, log)", fontsize=11, color=INK)
axL.set_xticks(x); axL.set_xticklabels(LABELS, fontsize=10)
axL.spines["top"].set_visible(False)
axL.grid(axis="y", color=GRID, lw=0.6); axL.set_axisbelow(True)

axR = axL.twinx()
axR.plot(x, SPEEDUP, color=C_SPD, lw=2.4, marker="o", markersize=9, markeredgecolor="white",
         markeredgewidth=1.5, zorder=6)
for xi, sp in zip(x, SPEEDUP):
    axR.text(xi, sp * 1.06, f"{sp:,.0f}×", ha="center", va="bottom", fontsize=10, fontweight="bold", color=C_SPD)
axR.set_ylim(0, max(SPEEDUP) * 1.28)
axR.set_ylabel("DIAMOND speedup over QuTiP  (×)", fontsize=11, color=C_SPD)
axR.tick_params(axis="y", colors=C_SPD)
axR.spines["right"].set_color(C_SPD); axR.spines["top"].set_visible(False)

axL.set_title("Data transfer & DIAMOND speedup vs QuTiP  (q=14)", fontsize=12.5, fontweight="bold", loc="center", pad=10)
axL.legend(handles=[Patch(fc=C_CSR, label="CSR transfer"), Patch(fc=C_CSD, label="CSD transfer"),
                    Line2D([0], [0], color=C_SPD, lw=2.4, marker="o", markersize=8, label="DIAMOND speedup")],
           loc="upper center", frameon=False, fontsize=9.5, ncol=3, bbox_to_anchor=(0.5, -0.10))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diamond_transfer_speedup")
fig.savefig(OUT + ".png", dpi=200, bbox_inches="tight", facecolor="white")
fig.savefig(OUT + ".pdf", bbox_inches="tight", facecolor="white")
print("wrote", OUT + ".{png,pdf}")
