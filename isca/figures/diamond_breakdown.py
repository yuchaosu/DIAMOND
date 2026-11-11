#!/usr/bin/env python3.11
"""DIAMOND per-component CYCLE breakdown (qmaxcut_14_4, q=14, 16x16 = 256 PE) @ 700 MHz.
Numbers measured from ./outputs/diamond (compute cyc, HBM bytes).
Pipeline model (HW address-generation): preprocessing (pair-setup/AGU), memory, and routing
all OVERLAP compute; makespan = compute + one-time fill/drain. Single latency panel (no energy).
"""
import matplotlib.pyplot as plt

# ---- measured (qmaxcut_14_4 @ 16x16, iter=4) ----
F_GHZ      = 0.700                        # PE clock 700 MHz
COMPUTE_CYC = 310068.0
HBM_MiB    = 528.33
S, P       = 16, 256
FILL_DRAIN_CYC = 2 * (S - 1) + 8          # netDiameter + ceil(log2 P) = 30 + 8

cyc_ns = lambda c: c / F_GHZ              # cycles -> ns at 700 MHz (1.4286 ns/cyc)
us     = lambda ns: ns / 1000.0

COMPUTE_NS = cyc_ns(COMPUTE_CYC)          # 442,954 ns
PREPROC_NS = COMPUTE_NS                   # AGU feeds P operand-pairs/cyc -> matches compute rate
HBM_NS     = HBM_MiB * 1024 * 1024 / 2048.0   # bytes / 2.048 TB/s (memory-system time, clock-independent)
FILL_NS    = cyc_ns(FILL_DRAIN_CYC)
MAKESPAN_NS = COMPUTE_NS + FILL_NS

# Okabe-Ito colorblind-safe palette
C_COMPUTE, C_PREP, C_MEM, C_ROUTE = "#0072B2", "#E69F00", "#009E73", "#D55E00"
INK, MUTED, GRID = "#1a1a1a", "#5a5a5a", "#d8d8d8"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "axes.edgecolor": MUTED, "axes.linewidth": 0.8,
                     "text.color": INK, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED})

fig, ax = plt.subplots(1, 1, figsize=(9.4, 3.9))

stages = [  # label, dur_ns, color, hidden?, note
    ("Compute  (MAC array)",           COMPUTE_NS, C_COMPUTE, False, "BOTTLENECK → sets makespan"),
    ("Preprocessing  (pair-setup/AGU)", PREPROC_NS, C_PREP,   True,  "hidden — feeds array at P/cyc"),
    ("Memory  (HBM)",                  HBM_NS,     C_MEM,     True,  "hidden — 0% exposed"),
    ("Routing  (reduce net)",          COMPUTE_NS, C_ROUTE,   True,  "hidden — throughput ≤ compute"),
]
h = 0.62
for i, (lab, dur, col, hidden, note) in enumerate(stages):
    y = len(stages) - 1 - i
    if hidden:
        ax.barh(y, us(dur), height=h, color=col, alpha=0.30,
                edgecolor=col, linewidth=1.3, hatch="///", zorder=2)
    else:
        ax.barh(y, us(dur), height=h, color=col, alpha=0.92,
                edgecolor="white", linewidth=1.5, zorder=3)
    ax.text(us(dur) + 6, y, note, va="center", ha="left", fontsize=9,
            color=INK if not hidden else MUTED, fontweight="bold" if not hidden else "normal")
    ax.text(-8, y, lab, va="center", ha="right", fontsize=10, color=INK)

mk = us(MAKESPAN_NS)
ax.axvline(mk, color=INK, ls="--", lw=1.2, zorder=5)
ax.text(mk, len(stages) - 0.30, f"  makespan = {mk:.0f} µs", va="bottom", ha="left",
        fontsize=10, fontweight="bold", color=INK)
ax.set_xlim(-135, mk * 1.34)
ax.set_ylim(-0.7, len(stages) - 0.05)
ax.set_yticks([])
ax.set_xlabel("time  (µs)  —  1 cycle = 1.43 ns @ 700 MHz", fontsize=10)
ax.set_title("DIAMOND cycle breakdown — qmaxcut, q=14, 16×16 (256 PE) @ 700 MHz",
             fontsize=12.5, fontweight="bold", loc="left", pad=12)
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.grid(axis="x", color=GRID, lw=0.6, zorder=0)
ax.set_axisbelow(True)
ax.text(0.0, -0.26,
        "Compute-bound: makespan = compute (%.0f µs) + one-time fill/drain (%.0f ns). "
        "Preprocessing, memory, and routing overlap compute → 0 exposed cycles."
        % (us(COMPUTE_NS), FILL_NS),
        transform=ax.transAxes, fontsize=8.5, color=MUTED)

fig.savefig("/tmp/claude-435053/diamond_breakdown_qmaxcut14.png", dpi=200, bbox_inches="tight",
            facecolor="white")
fig.savefig("/tmp/claude-435053/diamond_breakdown_qmaxcut14.pdf", bbox_inches="tight",
            facecolor="white")
print(f"saved. @700MHz: compute={us(COMPUTE_NS):.1f}us  preproc={us(PREPROC_NS):.1f}us  "
      f"HBM={us(HBM_NS):.1f}us  fill/drain={FILL_NS:.0f}ns  makespan={mk:.1f}us")
