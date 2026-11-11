#!/usr/bin/env python3.11
"""Discrete-event pipeline simulator with a REAL global cycle counter.

Records, on ONE shared cycle clock, the global start/end cycle of every stage of every power for the
chained operator build.  Four stages per power: Memory -> Compute -> Route -> Accumulate.

Stage COSTS are measured (not modeled):
  compute = compute_mac cycles (cycle-accurate PE loop in conv_breakdown)
  route   = gather_thr cycles   (reduction-network throughput)
  accum   = gather_thr cycles   (the reduce that follows the gather, same P-wide net)
  memory  = HBM bytes / 2.048 TB/s, converted to cycles at 700 MHz
  L (pipeline fill) = filldrain cycles = netDiameter + treeDepth  (measured first-tile traversal latency)

Event rules (a genuine schedule on the global clock, NOT a drawn heuristic):
  - each stage is a resource: it can hold one power at a time; freed when that power leaves it.
  - a stage of power k may START once (a) the feeder delivered its first tile — feeder_start + L —
    and (b) the stage is free from power k-1 (double-buffered pipeline).
  - a stage can never FINISH before its feeder delivered the last tile (+ L to drain it):
    end = max(start + own_dur, feeder_end + L).  A fast stage behind a slow feeder is data-starved.
  - powers advance on the SAME global counter (compute is the resource that serializes them).

Emits isca/gantt_real/timeline_<workload>.csv : power,stage,start_cyc,end_cyc,dur_cyc  (global cycles),
and prints the makespan.  Reads per-power costs from isca/figures/gantt_data/<name>.csv.
"""
import csv, os

F_GHZ = 0.700
BW_B_PER_NS = 2048.0
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "figures", "gantt_data")
STAGES = ["Memory", "Compute", "Route", "Accumulate"]
WORKLOADS = [("tfim_14.csv", "tfim_14"), ("qmaxcut_14.csv", "qmaxcut_14"), ("bh_14.csv", "bh_14")]


def load_costs(fname):
    """Per-power stage durations (cycles) + fill L (cycles). Memory bytes -> cycles at 700 MHz."""
    powers = []
    for r in csv.DictReader(open(os.path.join(SRC, fname))):
        mem_ns = (float(r["hbm_read_bytes"]) + float(r["hbm_write_bytes"])) / BW_B_PER_NS
        mem_cyc = mem_ns * F_GHZ
        comp = float(r["compute_mac_cyc"])
        gth = float(r["gather_thr_cyc"])
        L = float(r["filldrain_cyc"])                       # measured pipeline fill/drain latency
        powers.append({"dur": [mem_cyc, comp, gth, gth], "L": L})   # accum ~ gather (reduce net)
    return powers


def simulate(powers):
    """Discrete-event schedule on the global cycle counter. Returns events[k] = [(start,end)]*4."""
    free_at = [0.0] * 4                                     # per-stage resource free time (global cyc)
    events = []
    for k, p in enumerate(powers):
        dur, L = p["dur"], p["L"]
        start = [0.0] * 4
        end = [0.0] * 4
        for s in range(4):
            first_data = (start[s - 1] + L) if s > 0 else 0.0      # feeder's first tile arrived
            stage_free = free_at[s]                                # resource free from prev power
            start[s] = max(first_data, stage_free)
            feeder_end = end[s - 1] if s > 0 else start[s]
            end[s] = max(start[s] + dur[s], feeder_end + L)        # cannot finish before feeder delivered all
            free_at[s] = end[s]
        events.append(list(zip(start, end)))
    return events


def main():
    for fname, tag in WORKLOADS:
        path = os.path.join(SRC, fname)
        if not os.path.exists(path):
            print(f"skip {tag}: no {path}")
            continue
        powers = load_costs(fname)
        events = simulate(powers)
        makespan = max(e[3][1] for e in events)             # end of last Accumulate
        out = os.path.join(HERE, f"timeline_{tag}.csv")
        with open(out, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["power", "stage", "start_cyc", "end_cyc", "dur_cyc"])
            for k, e in enumerate(events):
                for s in range(4):
                    st, en = e[s]
                    w.writerow([k, STAGES[s], f"{st:.1f}", f"{en:.1f}", f"{en - st:.1f}"])
        print(f"{tag}: {len(powers)} powers, makespan {makespan:,.0f} cyc ({makespan / F_GHZ / 1e3:.2f} us) -> {os.path.basename(out)}")


if __name__ == "__main__":
    main()
