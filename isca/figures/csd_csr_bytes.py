#!/usr/bin/env python3.11
"""CSD vs CSR byte need for three q=14 matrices (tfim/diagonal, heis/banded, bh/fill-in).

CSD = CSR in diagonal view: identical value + per-nonzero index (8*nnz), the ONLY difference is the
pointer array -- CSR keeps one pointer per ROW (n), CSD one per occupied DIAGONAL (D).
  CSR = 8*nnz + 4*n     CSD = 8*nnz + 4*D    (value 4B fp32 + index 4B per nnz; pointer 4B)
Stacked bars isolate the shared payload (gray) from the pointer array (colored) so the saving is visible.
Data measured from the base Hamiltonians (embedded)."""
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

# base-H structure (measured): (label, nnz, n, D)
M = [("Diagonal\n(tfim)", 16384, 16384, 1),
     ("Banded\n(heis)", 122880, 16384, 27),
     ("Fill-in\n(bh)", 409600, 16384, 145)]
KB = 1024.0
C_SHARE, C_ROW, C_DIA = "#c7c7c7", "#08519c", "#E69F00"
INK, MUTED, GRID = "#1a1a1a", "#5a5a5a", "#dcdcdc"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": MUTED,
                     "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})

fig, ax = plt.subplots(1, 1, figsize=(8.2, 4.9))
x = np.arange(len(M)); w = 0.36
for i, (lab, nnz, n, D) in enumerate(M):
    share = 8 * nnz / KB
    row = 4 * n / KB
    dia = 4 * D / KB
    csr = share + row; csd = share + dia
    # CSR bar (left): shared + row-pointers
    ax.bar(i - w / 2, share, w, color=C_SHARE, edgecolor="white", linewidth=1.0, zorder=3)
    ax.bar(i - w / 2, row, w, bottom=share, color=C_ROW, edgecolor="white", linewidth=1.0, zorder=3)
    # CSD bar (right): shared + diagonal-pointers
    ax.bar(i + w / 2, share, w, color=C_SHARE, edgecolor="white", linewidth=1.0, zorder=3)
    ax.bar(i + w / 2, dia, w, bottom=share, color=C_DIA, edgecolor="white", linewidth=1.0, zorder=3)
    ax.text(i - w / 2, 40, "CSR", ha="center", va="bottom", fontsize=8.5, color="white", fontweight="bold", zorder=5)
    ax.text(i + w / 2, 40, "CSD", ha="center", va="bottom", fontsize=8.5, color="white", fontweight="bold", zorder=5)
    ax.text(i, max(csr, csd) + 90, f"CSD {csd/csr:.2f}×", ha="center", va="bottom", fontsize=10,
            color=INK, fontweight="bold")

ax.set_xticks(x); ax.set_xticklabels([m[0] for m in M], fontsize=10.5)
ax.set_ylabel("bytes to store the matrix  (KB)", fontsize=11)
ax.set_title("CSD vs CSR byte need  (q=14)", fontsize=12.5, fontweight="bold", loc="center", pad=10)
ax.set_ylim(0, 3700)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="y", color=GRID, lw=0.6); ax.set_axisbelow(True)
ax.legend(handles=[Patch(fc=C_SHARE, label="value + index  (8·nnz, shared)"),
                   Patch(fc=C_ROW, label="CSR row-pointers  (4·n)"),
                   Patch(fc=C_DIA, label="CSD diagonal-pointers  (4·D)")],
          loc="upper center", frameon=False, fontsize=9.3, ncol=1, bbox_to_anchor=(0.30, 0.99),
          handlelength=1.3)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diamond_csd_csr_bytes")
fig.savefig(OUT + ".png", dpi=200, bbox_inches="tight", facecolor="white")
fig.savefig(OUT + ".pdf", bbox_inches="tight", facecolor="white")
print("wrote", OUT + ".{png,pdf}")
for lab, nnz, n, D in M:
    csr = 8*nnz + 4*n; csd = 8*nnz + 4*D
    print(f"  {lab.split(chr(10))[0]:9s} CSR {csr/1024:8.1f} KB  CSD {csd/1024:8.1f} KB  ratio {csd/csr:.3f}  (rowptr {4*n/1024:.0f}KB -> diagptr {4*D/1024:.3f}KB)")
