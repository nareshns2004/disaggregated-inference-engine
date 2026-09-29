#!/usr/bin/env bash
# perftest ceiling sweep (TRANSPORT.md §2). Every transport number is normalised against this.
# Runs traffic on real NICs: only on hosts allowlisted in docs/ENVIRONMENT.md.
#
#   PEER=<host> DEV=mlx5_0 CUDA_DEV=0 scripts/ceiling_sweep.sh bench/results/<run_id>/ceiling
#   (start the matching server side on PEER first; see the loop below)
set -euo pipefail
OUT=${1:?usage: ceiling_sweep.sh <outdir>}
: "${PEER:?set PEER}" "${DEV:?set DEV (e.g. mlx5_0)}"
CUDA_DEV=${CUDA_DEV:-}          # empty = host memory ceiling (label it!)
SIZES=${SIZES:-"4096 16384 32768 65536 262144 1048576 4194304 16777216 67108864"}
QPS=${QPS:-"1 2 4 8"}
ITERS=${ITERS:-5000}

read -r -p "Run perftest against ${PEER} on ${DEV} (allowlisted host)? [y/N] " ok
[[ "${ok}" == "y" ]] || exit 1

mkdir -p "${OUT}"
cuda_flag=()
[[ -n "${CUDA_DEV}" ]] && cuda_flag=(--use_cuda="${CUDA_DEV}")   # add --use_cuda_dmabuf if ADR-0002 picks dmabuf

for qp in ${QPS}; do
  for sz in ${SIZES}; do
    ib_write_bw -d "${DEV}" -s "${sz}" -q "${qp}" -n "${ITERS}" --report_gbits -F \
      "${cuda_flag[@]}" "${PEER}" | tee "${OUT}/bw_s${sz}_q${qp}.txt"
  done
done
for sz in 64 4096 65536; do
  ib_write_lat -d "${DEV}" -s "${sz}" -n "${ITERS}" -F "${cuda_flag[@]}" "${PEER}" \
    | tee "${OUT}/lat_s${sz}.txt"
done
python3 scripts/env_manifest.py > "${OUT}/manifest.json"
echo "ceiling written to ${OUT}"
