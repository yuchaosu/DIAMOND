#!/usr/bin/env python3.11
"""Max-qubit reach: dense vs CSR vs DIA, iso-memory (141 GB), complex128 (16 B).
  dense:  16*n^2
  CSR:    20*nnz + 4*n          (16 val + 4 colindex per nnz, 4 rowptr per row)
  DIA:    16*D*n + 4*D          (dense-diagonal: full band + one offset per diagonal)
nnz depends on structure: diagonal D=1,nnz=n (full); banded D=128, ~5% band fill."""
import matplotlib.pyplot as plt
import numpy as np, math

B = 16; M = 141e9                       # complex128, iso-memory 141 GB (H200 & DIAMOND)
def maxq(bytes_fn):
    q = 1
    while bytes_fn(2**(q+1)) <= M: q += 1
    return q
dense = maxq(lambda n: B*n*n)
# diagonal (full): D=1, nnz=n
csr_d = maxq(lambda n: 20*n + 4*n)
dia_d = maxq(lambda n: B*1*n + 4*1)
# banded (densified ~5% full): D=128, nnz=0.05*128*n
Dp, fill = 128, 0.05
csr_b = maxq(lambda n: 20*int(fill*Dp*n) + 4*n)
dia_b = maxq(lambda n: 20*int(fill*Dp*n) + 4*Dp)   # sparse-diagonal: 16 val+4 pos per nnz, 4 offset per diag

INK, MUTED, GRID = "#1a1a1a", "#5a5a5a", "#dddddd"
C_DENSE, C_CSR, C_DIA = "#E69F00", "#6baed6", "#08519c"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": MUTED,
                     "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})

fig, ax = plt.subplots(1, 1, figsize=(9.4, 4.5))
groups = ["Dense\n(any structure)", "Diagonal H$^K$\n(full diagonals)", "Banded/fill-in H$^K$\n(~5% full)"]
x = np.arange(len(groups)); w = 0.34
# dense group: single bar; sparse groups: CSR + DIA
ax.bar(x[0], dense, width=w, color=C_DENSE, edgecolor="white", linewidth=1.3, zorder=3)
ax.text(x[0], dense+0.4, f"q{dense}", ha="center", va="bottom", fontsize=10, fontweight="bold")
for gi, (cq, dq) in [(1, (csr_d, dia_d)), (2, (csr_b, dia_b))]:
    ax.bar(x[gi]-w/2, cq, width=w, color=C_CSR, edgecolor="white", linewidth=1.3, zorder=3,
           label="CSR (scipy CPU)" if gi==1 else "")
    ax.bar(x[gi]+w/2, dq, width=w, color=C_DIA, edgecolor="white", linewidth=1.3, zorder=3,
           label="DIA (DIAMOND)" if gi==1 else "")
    ax.text(x[gi]-w/2, cq+0.4, f"q{cq}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.text(x[gi]+w/2, dq+0.4, f"q{dq}", ha="center", va="bottom", fontsize=10, fontweight="bold")
ax.bar(x[0], 0, color=C_DENSE, label="Dense (QuTiP CPU/GPU)")  # legend proxy

ax.axhspan(0, dense+0.5, color="#f0d9a8", alpha=0.25, zorder=0)
ax.text(2.42, dense-0.3, "dense ceiling", ha="right", va="top", fontsize=8.5, style="italic", color="#9a6a00")
ax.set_xticks(x); ax.set_xticklabels(groups, fontsize=10)
ax.set_ylim(0, 37); ax.set_ylabel("max qubits reachable  (q)", fontsize=11)
ax.set_title("Reach by data type — dense vs CSR vs DIA (iso-memory 141 GB, complex128)",
             fontsize=11.5, fontweight="bold", loc="left", pad=12)
ax.legend(frameon=False, fontsize=9, loc="lower right", ncol=1)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.grid(axis="y", color=GRID, lw=0.6); ax.set_axisbelow(True)
fig.text(0.01,-0.03,"Both sparse formats crush the dense wall (~q16). DIA replaces CSR's per-nnz colindex + per-row rowptr with one "
         "offset per diagonal (D<<n<<nnz) → DIA wins ~1 qubit. But the 16 B value dominates the total, so the big gap is "
         "sparse-vs-dense (~15 qubits), not DIA-vs-CSR (~1) → the accelerator earns its place on SPEED at that reach.",
         fontsize=7.8, color=MUTED)
fig.savefig("/tmp/claude-435053/diamond_reach_csr.png", dpi=200, bbox_inches="tight", facecolor="white")
fig.savefig("/tmp/claude-435053/diamond_reach_csr.pdf", bbox_inches="tight", facecolor="white")
print(f"dense q{dense} | diagonal CSR q{csr_d} DIA q{dia_d} | banded CSR q{csr_b} DIA q{dia_b}")
