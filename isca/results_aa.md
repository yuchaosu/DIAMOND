# A@A (K=1) sweep — HamLib q14–20 + SuiteSparse, DIAMOND vs all baselines

Single-step SpGEMM (`A@A`, `-iter=1`) over 48 workloads: the 44 non-dropped q14–20 rows of `isca/hamlib_provenance.csv` plus 4 SuiteSparse matrices (fv1, flowmeter0, tols4000, rdb5000) downloaded 2026-07-28 from sparse.tamu.edu and registered in the provenance table (`source=suitesparse`). All accelerator models on the same 16×16 PE mesh with HBM4 (`config/hbm4_sota.yaml`).

**Status (2026-07-30): complete.** 368/368 cells collected (job 267738), all `verify_aa.py` hard checks pass, DIAMOND-L3 fastest on every workload where it runs.

## Reproduction

```bash
python3 isca/convert_suitesparse.py            # .mtx -> DIA + .csr.npz + .meta under /mnt/beegfs/ysu34/hamlib/dia_suitesparse/
python3 isca/update_provenance_suitesparse.py  # source column + 4 rows in hamlib_provenance.csv (idempotent)
python3 isca/gen_manifest_aa.py                # -> isca/manifest_aa.txt (368 lines, headers cross-checked vs provenance)
sbatch --array=0-367%40 isca/sweep_aa.sbatch   # ran as job 267738 on 2026-07-30
python3 isca/merge_aa.py                       # -> compare_aa.csv + data_aa_*.csv
python3 isca/verify_aa.py                      # nnz / monotonicity / ranking checks
```

Methods per workload: `diamond_l1/l2/l3` (`outputs/diamond`, zeroskip/cbalance = 0/0, 1/0, 1/1), `tpu` (`outputs/HBMHamiltonianAnalytic -dataflow=tpu`, same runner as the 16×16 sweep), `traphs`/`trapms` (`outputs/accel_compare -only=Trapezoid-HS|Trapezoid-MS`), `segfold` (`isca/segfold/run_chain_segfold.py`), and `flex_op`/`flex_gust` (`isca/flexagon/run_chain.py`) for the 16 workloads with N < 65536 (STONNE hard-crashes at that dimension). 48×7 + 16×2 = 368 tasks, one exclusive node each. Cycles for the mesh methods are HBM-inclusive: `max(compute_cycles, hbm_time_ns)` at 1 GHz.

## Coverage

368/368 cells collected (`isca/compare_aa.csv`); 290 OK, 78 non-OK, all attributable:

| method | OK | non-OK | failure detail |
|---|---|---|---|
| diamond_l3 | 46 | 2 | OOM on vib_16_4, vib_18_4 only (nnz up to 156M) |
| diamond_l2 | 46 | 2 | OOM on vib_16_4, vib_18_4 |
| diamond_l1 | 38 | 10 | OOM: the 6 known heavies (bh_18/20, chem_14, Li2_14, O2_16, heis_20) + vib_14/16/18 + flowmeter0 — zeroskip-off materializes zeros even at K=1 |
| tpu | 48 | 0 | — |
| traphs | 46 | 2 | OOM on vib_16_4, vib_18_4 |
| trapms | 16 | 32 | 30 OOM + 2 TIMEOUT; first-ever trapms sweep — inner-product does not scale past q14 |
| segfold | 21 | 27 | 22 CRASH + 4 OOM + 1 TIMEOUT, all inside csegfold at the first multiply (`H^1`); same workload set that failed at K=4/5, plus the newer families (max3sat/maxkcut/vib). K=1 recovered 5 workloads that only failed at later densified steps (bh_14, chem_14, heis_14, Li2_14, qmaxcut_14) |
| flex_op | 15 | 1 | per-step 2 h timeout (vib_14_4) |
| flex_gust | 14 | 2 | per-step 2 h timeout (vib_14_4, Li2_14_6) |

## SuiteSparse results (cycles, 16×16 mesh, HBM-inclusive)

| method | tols4000 (N=4000, D=177) | rdb5000 (N=5000, D=7) | fv1 (N=9604, D=9) | flowmeter0 (N=9669, D=801) |
|---|---|---|---|---|
| diamond_l3 | **346** | **1,377** | **3,828** | **3,008** |
| diamond_l2 | 5,214 | 29,600 | 85,264 | 67,409 |
| diamond_l1 | 457,390 | 34,794 | 85,846 | OOM |
| segfold | 11,837 | 20,682 | 66,577 | 41,363 |
| traphs (Gustavson) | 26,497 | 119,409 | 268,362 | 502,220 |
| flex_op | 92,607 | 315,461 | 1,056,611 | 758,151 |
| flex_gust | 966,049 | 1,856,079 | 8,294,379 | 8,071,775 |
| trapms (inner-product) | 6,627,090 | 16,148,592 | 76,989,548 | 67,104,391 |
| tpu (dense MXU) | 252,000,000 | 492,980,008 | 3,480,532,836 | 3,550,808,525 |

Observations:

- DIAMOND-L3 is fastest on all four, 14–34× over the best baseline (SegFold in every case): 34× tols4000, 15× rdb5000, 17× fv1, 14× flowmeter0. These are classical sparse matrices (CFD, FEM, model reduction), not Hamiltonians, so the offset-space result transfers beyond HamLib.
- The L1→L2 gap isolates zeroskip on scattered-diagonal inputs: tols4000 (177 mostly-empty diagonals) pays 88× without it, flowmeter0 (801 diagonals) OOMs outright. On the tightly banded pair (D=7, D=9) L1≈L2.
- L2 cycles ≈ nnz exactly (fv1: 85,264 = its nnz) — expected for one MAC per nonzero with no compaction, a good measurement sanity signal.
- fv1 and flowmeter0 are `symmetric` MatrixMarket files; nnz after expansion (85,264 / 67,391) matches the SuiteSparse collection pages. tols4000 (N=4000 ≤ the 4096 verify cap) passed DIAMOND's functional check: `-verify=1` → max_abs_diff 5.8e-11, 0 mismatches.

## Verification status (`isca/verify_aa.py`) — all hard checks pass

- Check 1 — per-step operand nnz reported by Flexagon/SegFold equals provenance nnz: **pass** (all OK rows).
- Check 2 — K=1 cycles < K=4/5 cycles per (method, workload): 151 cells compared, **pass**; 14 cells skip against known-stale references (below).
- Check 3 — ranking: **no workload where any baseline beats diamond_l3** (0/48).

### Stale-reference investigation (resolved 2026-07-30)

Check 2 initially flagged 14 diamond_l3 cells on diagonal-class workloads (tfim/maxcut/reg3/tsp q14–20) where K=1 reported more cycles than the old K=4/5 rows — impossible for a chain if measured consistently. Root cause: **the old `data_16x16_DIAMOND.csv` rows for these cells are compute-only** (they predate the `max(compute, hbm_time_ns)` fold in `sweep_16x16.sbatch`); the A@A rows fold HBM, and for these compute-tiny cells HBM dominates. The new data is correct.

Repro (beegfs was down, so run node-locally): rebuild the driver with the input-root prefix made conditional (`sed` on `main/diamond.cpp:842`, linked against prebuilt `objs/*.o`), synthesize the tfim_14 pattern (`N 16384 D 1`, all-nonzero diagonal — cycle counts depend only on the nonzero pattern), run `-zeroskip=1 -cbalance=1` at both K:

| K | compute (cyc) | hbm (ns, csv field 13 = `st.cycles`, total over all iterations) | folded max |
|---|---|---|---|
| 1 | 102 | 512 | 512 — byte-identical to the sweep's tfim_14_4 diamond_l3 row |
| 4 | 408 — exactly the old `data_16x16` value | 1664 | 1664 |

Under consistent measurement K=4 (1664) > K=1 (512): monotonicity holds. The 14 cells are listed in `KNOWN_STALE_REF` in `verify_aa.py` and report as SKIP(stale-ref).

Follow-up: if the old diagonal-class DIAMOND rows in `data_16x16_DIAMOND.csv` are ever used for absolute (not relative) numbers, they understate runtime on compute-tiny cells — re-sweep K=4/5 with the current sbatch to refresh them.

## Files

- `isca/compare_aa.csv` — unified results (method, workload, q, K, class, source, pe, cycles, status, sec)
- `isca/data_aa_{DIAMOND,TPU,Trapezoid,flexagon,segfold}.csv` — per-tool, same shapes as the 16×16 set
- `isca/rows_aa/` — immutable raw per-task rows + job logs (job 267738)
- `isca/manifest_aa.txt` — the 368-task manifest
- `/mnt/beegfs/ysu34/hamlib/dia_suitesparse/` — converted DIA inputs (+ `.csr.npz`, `.txt.meta`); source tarballs kept at `/mnt/beegfs/ysu34/suitesparse/`
