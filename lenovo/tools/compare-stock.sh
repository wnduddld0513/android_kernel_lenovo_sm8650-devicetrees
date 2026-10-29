#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
# (C) 2026 The LineageOS Project
#
# Compare the dtb and dtbo.img built by kernelmk-flow.sh with the stock ones,
# semantically (phandles normalised, overlays flattened to their effect).
#
# usage: lenovo/tools/compare-stock.sh STOCK_DTB STOCK_DTBO_IMG BUILT_DTB BUILT_DTBO_IMG
#   STOCK_DTB       concatenated dtb of the stock vendor_boot (unmodified ROW)
#   STOCK_DTBO_IMG  stock dtbo.img
# The built dtb holds the four pineapple dtbs, which are stock entries 4-7
# (0-3 are cliffs, 8-10 volcano); the built dtbo.img holds the stock entries
# 36 (AVF) and 37 (lapis QRD).  Exit status 0 only if all of them are identical.
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
S=$(mktemp -d)
trap 'rm -rf "$S"' EXIT
python3 "$HERE/split_stock.py" "$1" "$2" "$S/stock"
python3 "$HERE/split_stock.py" "$3" "$4" "$S/built"
rc=0

echo "== base dtbs (dtcompare.py: nodes only in stock / only in build / property differences)"
for i in 0 1 2 3; do
	printf 'built %02d = stock %02d  ' "$i" $((i + 4))
	python3 "$HERE/dtcompare.py" "$S/stock/dtb/$(printf %02d $((i + 4))).dtb" "$S/built/dtb/$(printf %02d "$i").dtb" --summary || rc=1
done

echo "== dtbo entries (dtbo_cmp.py --effect: flattened target/node/property values)"
for i in 0 1; do
	printf 'built %02d = stock %02d  ' "$i" $((i + 36))
	python3 "$HERE/dtbo_cmp.py" "$S/stock/dtbo/$(printf %02d $((i + 36))).dtbo" "$S/built/dtbo/$(printf %02d "$i").dtbo" --effect --summary | tr '\n' ' '
	echo
done
exit $rc
