# SPDX-License-Identifier: GPL-2.0-only
# (C) 2026 The LineageOS Project
#
# Lenovo Yoga Tab Plus (TB520FU, lapis) device trees for the kernel build.
# lapis-pineapple*.dtb are the Qualcomm pineapple SoC dtbs with the TB520FU
# differences (bases for merge_dtbs.py); avf-overlay and lapis-qrd-overlay are
# the two board dtbos of the stock dtbo.img.  techpack/ holds the component
# overlays that merge_dtbs.py folds into the bases.
#
# BoardConfig:  BOARD_USES_QCOM_MERGE_DTBS_SCRIPT := true
#               TARGET_MERGE_DTBS_WILDCARD := lapis-pineapple*
#               TARGET_MERGE_DTBOS_WILDCARD := *-overlay

KBUILD_DTC_INCLUDE += $(addprefix $(srctree)/$(src)/../../sm8650-modules/qcom/opensource/, \
	audio-kernel/include camera-kernel synx-kernel display-drivers/include)

dtb-y += lapis-pineapple.dtb lapis-pineapple-v2.dtb \
	 lapis-pineapplep.dtb lapis-pineapplep-v2.dtb
dtbo-y += avf-overlay.dtbo lapis-qrd-overlay.dtbo

always-y	:= $(dtb-y) $(dtbo-y)
subdir-y	:= techpack
clean-files	:= *.dtb *.dtbo
