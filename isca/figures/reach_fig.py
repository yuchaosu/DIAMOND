#!/usr/bin/env python3.11
"""Max-qubit reach by data type. Store the propagator as complex128 (16 B/elem).
Dense: 16*4^q ; DIA (D occupied diagonals): 16*D*2^q. Wall = largest q fitting the budget.
GPU = NVIDIA H200 (141 GB HBM3e); CPU = 512 GB host; DIAMOND iso-memory with H200 (141 GB)."""
import matplotlib.pyplot as plt
import numpy as np, math

BYTES = 16                       # complex128
H200, CPU = 141e9, 512e9         # memory budgets
dense_wall = lambda M: math.floor(0.5 * math.log2(M / BYTES))
dia_wall   = lambda M, D: math.floor(math.log2(M / (BYTES * D)))

# (label, max_q, color, data_type)
C_DENSE, C_DIA_B, C_DIA_D = "#E69F00", "#6baed6", "#08519c"
rows = [
    ("QuTiP GPU  (H200, 141 GB) — dense",       dense_wall(H200),    C_DENSE),
    ("QuTiP CPU  (512 GB) — dense",             dense_wall(CPU),     C_DENSE),
    ("DIAMOND  (H200, 141 GB) — DIA, banded (D≈128)", dia_wall(H200,128), C_DIA_B),
    ("DIAMOND  (H200, 141 GB) — DIA, diagonal (D=1)",  dia_wall(H200,1),  C_DIA_D),
]
INK, MUTED, GRID = "#1a1a1a", "#5a5a5a", "#dddddd"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": MUTED,
                     "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})

fig, ax = plt.subplots(1, 1, figsize=(9.6, 4.3))
y = np.arange(len(rows))[::-1]
for i, (lab, q, col) in enumerate(rows):
    yy = y[i]
    ax.barh(yy, q, height=0.62, color=col, edgecolor="white", linewidth=1.4, zorder=3)
    ax.text(q + 0.4, yy, f"q = {q}", va="center", ha="left", fontsize=11, fontweight="bold", color=INK)
    ax.text(-0.4, yy, lab, va="center", ha="right", fontsize=9.7, color=INK)

# dense ceiling band
dmax = dense_wall(CPU)
ax.axvspan(0, dmax + 0.5, color="#f0d9a8", alpha=0.28, zorder=0)
ax.text(dmax/2, len(rows)-0.35, "dense ceiling (O(4$^q$))", ha="center", va="bottom", fontsize=8.5,
        color="#9a6a00", style="italic")

ax.set_xlim(0, 37); ax.set_ylim(-0.7, len(rows)-0.25); ax.set_yticks([])
ax.set_xlabel("max qubits reachable  (q)", fontsize=11)
ax.set_title("Operator-building reach by data type — iso-memory (same 141 GB for GPU & DIAMOND)",
             fontsize=12, fontweight="bold", loc="left", pad=12)
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0); ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
# arrows showing the gap
ax.annotate("", xy=(rows[3][1], y[3]+0.42), xytext=(dmax, y[3]+0.42),
            arrowprops=dict(arrowstyle="<->", color=MUTED, lw=1.1))
ax.text((dmax+rows[3][1])/2, y[3]+0.5, f"+{rows[3][1]-dmax} qubits (same memory)", ha="center", va="bottom",
        fontsize=8.5, color=MUTED)
fig.text(0.01, -0.03, "Store propagator as complex128 (16 B). Dense: 16·4$^q$ ≤ M. DIA: 16·D·2$^q$ ≤ M. "
         "GPU dense walls one qubit below CPU (less memory). DIA banded/fill-in is densification-limited "
         "(D grows with q); diagonal (D=1) is exact.", fontsize=8, color=MUTED)
fig.savefig("/tmp/claude-435053/diamond_reach.png", dpi=200, bbox_inches="tight", facecolor="white")
fig.savefig("/tmp/claude-435053/diamond_reach.pdf", bbox_inches="tight", facecolor="white")
print("walls:", [(r[0].split(' —')[0].strip(), r[1]) for r in rows])
