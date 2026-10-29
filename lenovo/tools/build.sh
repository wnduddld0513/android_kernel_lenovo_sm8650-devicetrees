#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
# (C) 2026 The LineageOS Project
#
# Build the Lenovo Yoga Tab Plus (TB520FU, lapis) device trees from this repo:
#
#   $OUT/dtb/<name>.dtb      base DTBs: qcom/<name>.dts, then every component
#                            overlay listed in lenovo/dtb.list applied with
#                            fdtoverlay (the same split the Qualcomm build
#                            uses between the SoC dtb and the subsystem dtbo)
#   $OUT/pineapple.dtb       all base DTBs concatenated in the order of
#                            lenovo/dtb.list (the layout of the vendor_boot dtb)
#   $OUT/dtbo/<idx>.dtbo     board overlays listed in lenovo/dtbo.list
#   $OUT/dtbo.img            mkdtboimg image of them (id/rev/custom = 0, the
#                            bootloader matches on the msm-id/board-id properties)
#
# usage: lenovo/tools/build.sh [dtb] [dtbo]       (default: both)
#
# Environment:
#   OUT              output directory                    (default: <repo>/out)
#   KERNEL_INCLUDE   kernel include/ with dt-bindings/   (default: ../sm8650/include)
#   MODULES          sm8650-modules qcom/opensource      (default: ../sm8650-modules/qcom/opensource)
#   CPP DTC FDTOVERLAY MKDTBOIMG   host tools
set -eu

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TOP=$(cd "$HERE/../.." && pwd)
OUT=${OUT:-$TOP/out}
KERNEL_INCLUDE=${KERNEL_INCLUDE:-$TOP/../sm8650/include}
MODULES=${MODULES:-$TOP/../sm8650-modules/qcom/opensource}
CPP=${CPP:-cpp}
DTC=${DTC:-dtc}
FDTOVERLAY=${FDTOVERLAY:-fdtoverlay}
MKDTBOIMG=${MKDTBOIMG:-mkdtboimg}
QCOM=$TOP/qcom

INCLUDES=(-I "$QCOM" -I "$KERNEL_INCLUDE"
	-I "$MODULES/audio-kernel/include" -I "$MODULES/camera-kernel"
	-I "$MODULES/synx-kernel" -I "$MODULES/display-drivers/include")

# compile SRC.dts (path relative to qcom/) to DST.dtb/.dtbo with -@ symbols
compile() {
	local src=$QCOM/$1 dst=$2 dir
	dir=$(dirname "$src")
	mkdir -p "$(dirname "$dst")"
	$CPP -nostdinc -undef -D__DTS__ -x assembler-with-cpp "${INCLUDES[@]}" -I "$dir" \
		-o "$dst.pp" "$src"
	$DTC -q -@ -I dts -O dtb -b 0 -i "$dir" -i "$QCOM" -o "$dst" "$dst.pp"
	rm -f "$dst.pp"
}

build_dtb() {
	mkdir -p "$OUT/dtb"
	: > "$OUT/pineapple.dtb"
	local name base comps c ovl
	grep -v '^[[:space:]]*\(#\|$\)' "$HERE/../dtb.list" | while read -r name base comps; do
		compile "$base" "$OUT/dtb/$name.base"
		ovl=()
		for c in $comps; do
			compile "$c" "$OUT/dtb/$(echo "$c" | tr '/.' '__').dtbo"
			ovl+=("$OUT/dtb/$(echo "$c" | tr '/.' '__').dtbo")
		done
		if [ ${#ovl[@]} -gt 0 ]; then
			$FDTOVERLAY -i "$OUT/dtb/$name.base" -o "$OUT/dtb/$name.dtb" "${ovl[@]}"
		else
			cp "$OUT/dtb/$name.base" "$OUT/dtb/$name.dtb"
		fi
		cat "$OUT/dtb/$name.dtb" >> "$OUT/pineapple.dtb"
		echo "dtb  $name"
	done
}

build_dtbo() {
	mkdir -p "$OUT/dtbo"
	local idx src imgs=()
	while read -r idx src; do
		compile "$src" "$OUT/dtbo/$idx.dtbo"
		imgs+=("$OUT/dtbo/$idx.dtbo")
		echo "dtbo $idx $src"
	done < <(grep -v '^[[:space:]]*\(#\|$\)' "$HERE/../dtbo.list" | sort -n)
	$MKDTBOIMG create "$OUT/dtbo.img" --page_size=4096 "${imgs[@]}"
}

targets=${*:-dtb dtbo}
for t in $targets; do
	case $t in
	dtb) build_dtb ;;
	dtbo) build_dtbo ;;
	*) echo "unknown target $t" >&2; exit 1 ;;
	esac
done
