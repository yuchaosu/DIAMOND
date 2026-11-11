#!/usr/bin/env python3.11
"""CSR vs CSD memory transfer for the chained operator build H^1..H^(K+1), q=14..20.

Both formats store only the true nonzeros with CSR's logic (value + per-nnz index + a pointer array);
they differ ONLY in the pointer array — CSR keys by row (nrows pointers), CSD keys by diagonal
(D pointers). value = 4 B fp32; indices/pointers = 4 B int32.
  CSR / matrix = 8*nnz + 4*nrows      (nrows == n here: every row has a nonzero)
  CSD / matrix = 8*nnz + 4*D          (D = occupied diagonals)
Bytes MOVED use DIAMOND's non-fused HBM event model (initial read H; per power read prev + re-read H
+ write new). Recomputed exactly from the measured per-power nnz_seq / D_seq in
result/dia_csr_transfer_q14-20.csv (no re-simulation)."""
import csv, os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

REPO = "/home/ysu34/DIAMOND/diamond"
SRC = os.path.join(REPO, "result", "dia_csr_transfer_q14-20.csv")
ORDER = ["diagonal", "banded", "fill-in"]
MiB = 1024.0 * 1024.0


def transfer(seq_mat):
    base = seq_mat[0]; total = base
    for i in range(len(seq_mat) - 1):
        total += seq_mat[i] + base + seq_mat[i + 1]
    return total


rows = []
with open(SRC) as f:
    for r in csv.DictReader(f):
        if not r["nnz_seq"] or not r["D_seq"]:
            continue
        nnz = [int(x) for x in r["nnz_seq"].split("|")]
        D = [int(x) for x in r["D_seq"].split("|")]
        n = int(r["n"])
        csd = transfer([8 * z + 4 * d for z, d in zip(nnz, D)]) / MiB       # 8*nnz + 4*D
        cse = transfer([8 * z + 4 * n for z in nnz]) / MiB                  # CSR: 8*nnz + 4*nrows(=n)
        rows.append((r["class"], int(r["q"]), r["workload"].rsplit("_", 1)[0], csd, cse))
rows.sort(key=lambda x: (ORDER.index(x[0]), x[1]))

C_CSR, C_CSD = "#6baed6", "#08519c"        # CSR (light) vs CSD (deep blue)
INK, MUTED, GRID = "#1a1a1a", "#5a5a5a", "#dcdcdc"
CLS_C = {"diagonal": "#2b8cbe", "banded": "#E69F00", "fill-in": "#CC79A7"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10.5, "axes.edgecolor": MUTED,
                     "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})

fig, ax = plt.subplots(1, 1, figsize=(9.2, 5.0))
y = np.arange(len(rows))[::-1]; h = 0.36
for yy, (cls, q, fam, csd, cse) in zip(y, rows):
    ax.barh(yy + h / 2, cse, height=h, color=C_CSR, edgecolor="white", linewidth=1.1, zorder=3)
    ax.barh(yy - h / 2, csd, height=h, color=C_CSD, edgecolor="white", linewidth=1.1, zorder=3)
    ratio = csd / cse
    ax.text(max(csd, cse) * 1.12, yy, f"CSD {ratio:.2f}×", va="center", ha="left",
            fontsize=8.6, color=INK, fontweight="bold")
    ax.text(-0.02, yy, f"{fam}  q{q}", transform=ax.get_yaxis_transform(), va="center", ha="right",
            fontsize=9.4, color=INK)

seen = {}
for yy, (cls, *_1) in zip(y, rows):
    seen.setdefault(cls, []).append(yy)
for cls, ys in seen.items():
    ax.text(-0.185, sum(ys) / len(ys), cls, transform=ax.get_yaxis_transform(), va="center", ha="center",
            rotation=90, fontsize=10, fontweight="bold", color=CLS_C[cls])
    ax.plot([-0.16, -0.16], [min(ys) - 0.42, max(ys) + 0.42], transform=ax.get_yaxis_transform(),
            color=CLS_C[cls], lw=2.4, solid_capstyle="round", clip_on=False, zorder=5)

ax.set_xscale("log"); ax.set_xlim(0.5, 3e6)
ax.set_ylim(-0.7, len(rows) - 0.3); ax.set_yticks([])
ax.set_xlabel("memory transferred to build the operator   (MiB, log)", fontsize=10.5)
ax.set_title("CSR vs CSD transfer", fontsize=12.5, fontweight="bold", loc="center", pad=10)
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0); ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
ax.legend(handles=[Patch(fc=C_CSR, label="CSR  (row pointers, n)"),
                   Patch(fc=C_CSD, label="CSD  (diagonal pointers, D)")],
          loc="upper center", frameon=False, fontsize=9.5, ncol=2, bbox_to_anchor=(0.5, -0.12))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diamond_transfer")
fig.savefig(OUT + ".png", dpi=200, bbox_inches="tight", facecolor="white")
fig.savefig(OUT + ".pdf", bbox_inches="tight", facecolor="white")
print("wrote", OUT + ".{png,pdf}  rows:", len(rows))
for cls, q, fam, csd, cse in rows:
    print(f"  {fam:10s} q{q}: CSD {csd:12.2f}  CSR {cse:12.2f}  ratio {csd/cse:.3f}")
