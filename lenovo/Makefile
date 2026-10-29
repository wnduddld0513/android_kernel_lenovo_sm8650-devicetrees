# SPDX-License-Identifier: GPL-2.0-only
# (C) 2026 The LineageOS Project
#
# Lenovo Yoga Tab Plus (TB520FU, lapis) device trees for the kernel build.
# The Qualcomm SoC dtbs and the subsystem overlays come from ../qcom (see
# ../qcom/Makefile); the lapis-pineapple*.dtb here are the same SoC dtbs with
# the TB520FU differences, and the dtbos are the lapis board, Lenovo, AVF, BT
# and camera overlays.  lenovo/dtb.list and lenovo/dtbo.list name which
# overlays make up the vendor_boot dtb and the dtbo.img of the stock image;
# lenovo/tools/build.sh builds the same sources without a kernel tree.

LAPIS_BASE_DTB += lapis-pineapple.dtb lapis-pineapple-v2.dtb
LAPIS_APQ_BASE_DTB += lapis-pineapplep.dtb lapis-pineapplep-v2.dtb

LAPIS_BOARDS += pineapple-lenovo-overlay.dtbo \
		avf-overlay.dtbo \
		lapis-qrd-overlay.dtbo \
		lapis-kiwi-bt.dtbo \
		lapis-camera.dtbo \
		lapis-camera-v2.dtbo

dtb-y += $(LAPIS_BOARDS) $(LAPIS_BASE_DTB) $(LAPIS_APQ_BASE_DTB)

always-y	:= $(dtb-y)
clean-files	:= *.dtb *.dtbo
