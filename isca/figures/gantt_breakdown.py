#!/usr/bin/env python3.11
"""DIAMOND pipeline Gantt — per-iteration compute / memory(HBM) / routing(gather), q=14, 16x16.

Measured per power by outputs/conv_breakdown (--gantt): compute_mac, gather_thr, filldrain cycles and
HBM read/write bytes. Preprocessing EXCLUDED (per request). Time axis in each panel is that workload's
own scale (the three patterns span ns -> ms).

Overlap model (== diamond.cpp:1020 makespan): the K powers pipeline under double-buffering, so the
COMPUTE lane and the MEMORY(HBM) lane run concurrently from t=0; routing(gather) overlaps compute
(reduction net at P adds/cyc). makespan = max(compute+filldrain, memory); routing hides inside compute.
Overlap window = [0, min(compute,memory)]; the tail of the longer lane is EXPOSED (the real bottleneck).
"""
import csv, os
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

F_GHZ = 0.700                              # PE clock 700 MHz -> 1 cyc = 1.4286 ns
BW    = 2048.0                             # HBM4 2.048 TB/s = 2048 B/ns
cyc_ns = lambda c: c / F_GHZ
GDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gantt_data")
PANELS = [("tfim_14.csv",    "Diagonal  (tfim, D=1)"),
          ("qmaxcut_14.csv", "Banded  (qmaxcut)"),
          ("bh_14.csv",      "Fill-in  (bh)")]

# Okabe-Ito (CVD-safe; same trio as the other figures). Exposed = reserved red highlight.
C_COMPUTE, C_MEM, C_ROUTE = "#0072B2", "#009E73", "#E69F00"
C_EXPOSED = "#D55E00"
INK, MUTED, GRID, HIDE = "#1a1a1a", "#5a5a5a", "#dcdcdc", "#eeeeee"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": MUTED,
                     "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})


def load(path):
    comp, rout, fill, mem = [], [], [], []
    with open(path) as f:
        for r in csv.DictReader(f):
            comp.append(cyc_ns(float(r["compute_mac_cyc"])))
            rout.append(cyc_ns(float(r["gather_thr_cyc"])))
            fill.append(cyc_ns(float(r["filldrain_cyc"])))
            mem.append((float(r["hbm_read_bytes"]) + float(r["hbm_write_bytes"])) / BW)
    return comp, rout, fill, mem


def fmt_t(ns):
    return f"{ns:.0f} ns" if ns < 1e3 else (f"{ns/1e3:.1f} µs" if ns < 1e6 else f"{ns/1e6:.2f} ms")


def lane(ax, y, durs, color, h=0.58, hatch=None, alpha=0.95):
    cum = 0.0
    for d in durs:
        ax.barh(y, d, left=cum, height=h, color=color, alpha=alpha, edgecolor="white",
                linewidth=1.1, hatch=hatch, zorder=3)
        cum += d
    return cum


def has_rows(path):
    try:
        with open(path) as f:
            return sum(1 for _ in f) >= 2       # header + >=1 data row
    except OSError:
        return False

panels = [(p, t) for p, t in PANELS if has_rows(os.path.join(GDIR, p))]
fig, axes = plt.subplots(len(panels), 1, figsize=(9.6, 2.05 * len(panels)))
if len(panels) == 1:
    axes = [axes]

# 4 pipeline stages, top->bottom. Accumulate = reduce of the gathered cross-PE partials (same P-wide
# reduction network as Gather -> same per-power throughput). Okabe-Ito, CVD-safe.
STAGES = [("Memory", C_MEM), ("Compute", C_COMPUTE), ("Route", C_ROUTE), ("Accumulate", "#CC79A7")]
YROW = {0: 3, 1: 2, 2: 1, 3: 0}   # stage index -> y row (Memory on top)


FILL = 0.15   # first data / last-tile latency as a fraction of a stage: a downstream stage starts
              # once the feeder's first tile arrives, and finishes one tile after the feeder's last.


def schedule(dur):
    """dur[k] = [mem,comp,gather,accum] per power. Fine-grained software pipeline with a
    THROUGHPUT constraint: a stage can start once its feeder's first tile arrives, but it can
    never FINISH before the feeder delivered the last tile (+ one tile to drain). So a fast stage
    behind a slow feeder is data-starved and stretches to the feeder's span (e.g. compute on a
    memory-bound diagonal), never ending early. Returns (start, end) per [k][s]."""
    K = len(dur)
    start = [[0.0] * 4 for _ in range(K)]
    end = [[0.0] * 4 for _ in range(K)]
    for k in range(K):
        for s in range(4):
            first_data = start[k][s - 1] + FILL * dur[k][s - 1] if s > 0 else 0.0
            stage_free = end[k - 1][s] if k > 0 else 0.0                       # resource free after prev power
            start[k][s] = max(first_data, stage_free)
            feeder_end = end[k][s - 1] if s > 0 else start[k][s]
            drain = FILL * dur[k][s]                                           # process the feeder's last tile
            end[k][s] = max(start[k][s] + dur[k][s], feeder_end + drain)       # cannot finish before feeder done
    return start, end


for ax, (fname, title) in zip(axes, panels):
    comp, rout, fill, mem = load(os.path.join(GDIR, fname))
    K = len(comp)
    dur = [[mem[k], comp[k] + fill[k], rout[k], rout[k]] for k in range(K)]   # accum ~ gather (reduce net)
    start, end = schedule(dur)
    makespan = max(end[k][s] for k in range(K) for s in range(4))
    sc = 1.0 / makespan                                          # normalize: makespan = 1.0

    for k in range(K):
        for s in range(4):
            x0, w = start[k][s] * sc, (end[k][s] - start[k][s]) * sc
            ax.barh(YROW[s], w, left=x0, height=0.6, color=STAGES[s][1], edgecolor="white",
                    linewidth=1.0, zorder=3)
    ax.axvline(1.0, color=INK, ls="--", lw=1.1, zorder=5)

    ax.set_yticks([YROW[s] for s in range(4)]); ax.set_yticklabels([STAGES[s][0] for s in range(4)], fontsize=9)
    ax.set_ylim(-0.6, 3.7); ax.set_xlim(0, 1.05); ax.set_xticks([])
    ax.set_title(title, fontsize=10.5, fontweight="bold", loc="left", pad=5, color=INK)
    for sp in ("top", "right", "left", "bottom"): ax.spines[sp].set_visible(False)
    ax.tick_params(axis="both", length=0)

fig.legend(handles=[Patch(fc=c, label=lab) for lab, c in STAGES],
           loc="lower center", frameon=False, fontsize=9.5, ncol=4, bbox_to_anchor=(0.5, -0.005))
fig.tight_layout(rect=[0, 0.045, 1, 0.99])
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diamond_gantt_q14")
fig.savefig(OUT + ".png", dpi=200, bbox_inches="tight", facecolor="white")
fig.savefig(OUT + ".pdf", bbox_inches="tight", facecolor="white")
print("wrote", OUT + ".{png,pdf}")
print("saved gantt for panels:", [p for p, _ in panels])
