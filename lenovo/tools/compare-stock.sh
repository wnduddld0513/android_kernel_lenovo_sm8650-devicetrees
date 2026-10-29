#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
# (C) 2026 The LineageOS Project
#
# Compare the blobs built by build.sh with the stock ones, semantically.
#
# usage: lenovo/tools/compare-stock.sh STOCK_DTB STOCK_DTBO_IMG [dtb|dtbo]
#   STOCK_DTB       concatenated dtb of the stock vendor_boot (unmodified ROW)
#   STOCK_DTBO_IMG  stock dtbo.img
# STOCK_DTB_FIRST (default 4) is the index of the first built dtb in the stock
# vendor_boot dtb (0-3 are cliffs, 8-10 volcano).  Needs a finished build in $OUT (default <repo>/out).  Exit status 0 only if
# everything that is built is identical to its stock counterpart.
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TOP=$(cd "$HERE/../.." && pwd)
OUT=${OUT:-$TOP/out}
W=$(mktemp -d)
trap 'rm -rf "$W"' EXIT
python3 "$HERE/split_stock.py" "$1" "$2" "$W"
rc=0

if [ "${3:-dtb}" = dtb ] || [ -z "${3:-}" ]; then
	echo "== base dtbs (dtcompare.py: nodes only in stock / only in build / property differences)"
	i=${STOCK_DTB_FIRST:-4}
	while read -r name _; do
		printf '%-14s stock %02d  ' "$name" "$i"
		python3 "$HERE/dtcompare.py" "$W/dtb/$(printf %02d $i).dtb" "$OUT/dtb/$name.dtb" --summary || rc=1
		i=$((i + 1))
	done < <(grep -v '^[[:space:]]*\(#\|$\)' "$HERE/../dtb.list")
fi

if [ "${3:-dtbo}" = dtbo ] || [ -z "${3:-}" ]; then
	echo "== dtbo entries (dtbo_cmp.py --effect: flattened target/node/property values)"
	while read -r idx _; do
		printf 'entry %-3s ' "$idx"
		python3 "$HERE/dtbo_cmp.py" "$W/dtbo/$(printf %02d "$idx").dtbo" "$OUT/dtbo/$idx.dtbo" --effect --summary | tr '\n' ' '
		echo
	done < <(grep -v '^[[:space:]]*\(#\|$\)' "$HERE/../dtbo.list" | sort -n)
fi
exit $rc
