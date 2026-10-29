#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
# (C) 2026 The LineageOS Project
#
# Build the TB520FU (lapis) dtb and dtbo.img the way vendor/lineage
# build/tasks/kernel.mk does with BOARD_USES_QCOM_MERGE_DTBS_SCRIPT := true:
#
#   make dtbs  ->  mv arch/arm64/boot/dts/vendor/*/*.dtb{,o} $BASE/
#   merge_dtbs.py --base $BASE --techpack .../dts/vendor --out $MERGED
#   cat $(find $MERGED -name "$TARGET_MERGE_DTBS_WILDCARD.dtb" | sort)  > $OUT/dtb
#   mkdtboimg create $OUT/dtbo.img --page_size=4096 \
#       $(find $MERGED -name "$TARGET_MERGE_DTBOS_WILDCARD.dtbo" | sort)
#
# usage: lenovo/tools/kernelmk-flow.sh KERNEL_SRC
#   KERNEL_SRC  kernel tree (kernel/lenovo/sm8650, branch lineage-24.0-clo or
#               later) whose arch/arm64/boot/dts/vendor links to this repo
# Environment:
#   OUT          output directory                          (default: ./out-kernelmk)
#   HOST_BIN     directory with fdtget fdtput fdtoverlay fdtoverlaymerge
#                ufdt_apply_overlay (LineageOS external/dtc, system/libufdt)
#   MERGE_DTBS   vendor/lineage/build/tools/merge_dtbs.py
#   MKDTBOIMG    system/libufdt/utils/src/mkdtboimg.py (run with python3)
#   TARGET_MERGE_DTBS_WILDCARD   (default: lapis-pineapple*)
#   TARGET_MERGE_DTBOS_WILDCARD  (default: *-overlay)
#   DTC HOSTCC CC   host tools of the kernel build (default dtc/gcc/gcc)
set -eu

KERNEL_SRC=$(cd "$1" && pwd)
OUT=$(mkdir -p "${OUT:-out-kernelmk}" && cd "${OUT:-out-kernelmk}" && pwd)
: "${HOST_BIN:?}" "${MERGE_DTBS:?}" "${MKDTBOIMG:?}"
TARGET_MERGE_DTBS_WILDCARD=${TARGET_MERGE_DTBS_WILDCARD:-lapis-pineapple*}
TARGET_MERGE_DTBOS_WILDCARD=${TARGET_MERGE_DTBOS_WILDCARD:-*-overlay}
export LC_ALL=C PATH=$HOST_BIN:$PATH

DTB_OUT=$OUT/kernel
DTBS_BASE=$DTB_OUT/base
DTBS_OUT=$DTB_OUT/out
DTS=$DTB_OUT/arch/arm64/boot/dts
rm -rf "$DTB_OUT"
mkdir -p "$DTBS_BASE" "$DTBS_OUT"

KMAKE=(make -j"$(nproc)" -C "$KERNEL_SRC" O="$DTB_OUT" ARCH=arm64
	CC="${CC:-gcc}" HOSTCC="${HOSTCC:-gcc}" DTC="${DTC:-dtc}")
"${KMAKE[@]}" gki_defconfig vendor/lapis_GKI.config
"${KMAKE[@]}" dtbs

mv "$DTS"/vendor/*/*.dtb "$DTS"/vendor/*/*.dtbo "$DTBS_BASE"/
python3 "$MERGE_DTBS" --base "$DTBS_BASE" --techpack "$DTS/vendor" --out "$DTBS_OUT"

find "$DTBS_OUT" -type f -name "${TARGET_MERGE_DTBS_WILDCARD}.dtb" | sort | xargs cat > "$OUT/dtb"
python3 "$MKDTBOIMG" create "$OUT/dtbo.img" --page_size=4096 \
	$(find "$DTBS_OUT" -type f -name "${TARGET_MERGE_DTBOS_WILDCARD}.dtbo" | sort)
echo "dtb:      $OUT/dtb"
echo "dtbo.img: $OUT/dtbo.img"
