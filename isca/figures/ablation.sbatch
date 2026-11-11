#!/bin/bash
#SBATCH -J dia_ablation
#SBATCH -o /home/ysu34/DIAMOND/diamond/isca/figures/ablation_rows/log_%A_%a.out
#SBATCH --partition=turin,turin128,rome,genoa,milan,siena,cascade,skylake,normal
#SBATCH -N 1 -n 1 --cpus-per-task=2
#SBATCH --exclusive
#SBATCH --exclude=c12
#SBATCH -t 12:00:00
set -u
REPO=/home/ysu34/DIAMOND/diamond; cd "$REPO"
export PATH=/opt/ohpc/pub/compiler/gcc/12.4.0/bin:$PATH
export LD_LIBRARY_PATH=/opt/ohpc/pub/compiler/gcc/12.4.0/lib64:$REPO/external/ramulator2:${LD_LIBRARY_PATH:-}
export RAMULATOR_HBM_CONFIG=$REPO/config/hbm4_sota.yaml
MAN=$REPO/isca/figures/ablation_manifest.txt
OUT=$REPO/isca/figures/ablation_rows
line=$(sed -n "$((SLURM_ARRAY_TASK_ID+1))p" "$MAN")
IFS='|' read -r folder file cls lvl zs cb <<< "$line"
res=$(timeout 11h ./outputs/diamond -row=16 -col=16 -folder=$folder/ -file=$file.txt \
        -qubit=14 -iter=4 -zeroskip=$zs -cbalance=$cb -verify=0 2>&1 | grep '\[conv\]' | head -1)
echo "$cls|$file|$lvl|$res" > $OUT/row_${SLURM_ARRAY_TASK_ID}.txt
echo "done $cls $lvl -> $res"
