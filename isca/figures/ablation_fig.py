#!/usr/bin/env python3.11
"""Figure 2 (normalized): l1/l2/l3 ablation per matrix pattern. Compute cycles normalized
to l3 (full DIAMOND = 1x), so the optimization leverage is comparable across patterns.
Measured from outputs/diamond, 16x16 (256 PE), q=14. l1=baseline, l2=+zeroskip, l3=+cbalance."""
import matplotlib.pyplot as plt
import numpy as np

# raw compute cycles: l1, l2, l3  (None = did not finish)
RAW = [("Diagonal\n(tfim)", [65536, 65536, 408]),
       ("Banded\n(qmaxcut)", [28253550, 3998720, 310068]),
       ("Fill-in\n(bh)", [None, 17207059, 3716200])]
# normalize each pattern to its l3
ABL = [(lab, [ (v[j]/v[2] if v[j] is not None else None) for j in range(3) ]) for lab, v in RAW]

L_COL = ["#c6dbef", "#6baed6", "#08519c"]
INK, MUTED, GRID = "#1a1a1a", "#5a5a5a", "#dddddd"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": MUTED,
                     "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})

fig, axB = plt.subplots(1, 1, figsize=(7.4, 4.1))
x = np.arange(len(ABL)); w = 0.26
for j, lvl in enumerate(["l1  (baseline)", "l2  (+zeroskip)", "l3  (+cbalance)"]):
    vals = [a[1][j] for a in ABL]; xs = x + (j - 1) * w
    pl = [(xi, v) for xi, v in zip(xs, vals) if v is not None]
    axB.bar([p[0] for p in pl], [p[1] for p in pl], width=w, color=L_COL[j], edgecolor="white",
            linewidth=1.0, label=lvl, zorder=3)
    for xi, v in zip(xs, vals):
        if v is None:
            axB.text(xi, 3, "DNF", rotation=90, va="bottom", ha="center", fontsize=8, color=MUTED)
        elif v >= 2:
            axB.text(xi, v * 1.08, f"{v:.0f}×", va="bottom", ha="center", fontsize=8, color=INK, fontweight="bold")
axB.axhline(1, color=MUTED, ls="--", lw=0.9, zorder=1)
axB.set_yscale("log"); axB.set_ylim(0.7, 320)
axB.set_xticks(x); axB.set_xticklabels([a[0] for a in ABL], fontsize=10)
axB.set_ylabel("compute cycles  ÷  l3   (×, log)", fontsize=10)
axB.set_title("Ablation (normalized to l3): optimization leverage vs. pattern  (q=14, 16×16)",
              fontsize=11, fontweight="bold", loc="left", pad=10)
axB.text(len(ABL)-0.5, 1.06, "l3 = full DIAMOND (1×)", ha="right", va="bottom", fontsize=8, color=MUTED)
axB.legend(frameon=False, fontsize=9, loc="upper right")
for s in ("top", "right"): axB.spines[s].set_visible(False)
axB.grid(axis="y", color=GRID, lw=0.6); axB.set_axisbelow(True)
fig.text(0.01, -0.02, "Height = cycles relative to l3. Diagonal: zeroskip is a no-op (l1=l2), all 161× is cbalance. "
         "Banded: zeroskip 7× then cbalance 13×. Fill-in l1 did not finish (DNF).", fontsize=8, color=MUTED)
fig.savefig("/tmp/claude-435053/diamond_ablation.png", dpi=200, bbox_inches="tight", facecolor="white")
fig.savefig("/tmp/claude-435053/diamond_ablation.pdf", bbox_inches="tight", facecolor="white")
print("normalized ablation saved. l1/l2 vs l3:", [(a[0].split(chr(10))[0], a[1]) for a in ABL])
