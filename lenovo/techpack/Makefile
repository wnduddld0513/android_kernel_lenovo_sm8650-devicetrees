# SPDX-License-Identifier: GPL-2.0-only
# (C) 2026 The LineageOS Project
#
# Component ("techpack") overlays of the TB520FU (lapis) dtbs.  They are
# built one directory below lenovo/ so that merge_dtbs.py of the LineageOS
# kernel.mk treats them as techpacks and folds those whose msm-id/board-id
# match into the lapis-pineapple*.dtb bases, as the stock dtb has them.
# Most are the unchanged Qualcomm overlays of ../../qcom (one-line wrappers);
# lapis-kiwi-bt, lapis-camera*, lapis-vidc* replace or amend Qualcomm ones (the
# Qualcomm bt and camera overlays are not built here) and
# pineapple-lenovo-overlay holds the remaining Lenovo changes to the base.
# merge_dtbs.py applies overlays in an arbitrary order, so every overlay here
# only touches nodes of the base dtb or defined in the same overlay.

KBUILD_DTC_INCLUDE += $(addprefix $(srctree)/$(src)/../../../sm8650-modules/qcom/opensource/, \
	audio-kernel/include camera-kernel synx-kernel display-drivers/include)

dtbo-y += pineapple-audio.dtbo \
	   pineapple-ipa.dtbo \
	   pineapple-sde.dtbo \
	   pineapple-dsp.dtbo \
	   pineapple-eva.dtbo \
	   pineapple-eva-v2.dtbo \
	   pineapple-gpu.dtbo \
	   pineapple-v2-gpu.dtbo \
	   pineapple-ubwcp.dtbo \
	   pineapple-hw-fence.dtbo \
	   pineapple-mmrm.dtbo \
	   pineapple-mmrm-test.dtbo \
	   pineapple-mmrm-test-v2.dtbo \
	   pineapple-synx.dtbo \
	   lapis-vidc.dtbo \
	   lapis-vidc-v2.dtbo \
	   lapis-kiwi-bt.dtbo \
	   lapis-camera.dtbo \
	   lapis-camera-v2.dtbo \
	   pineapple-lenovo-overlay.dtbo

always-y	:= $(dtbo-y)
clean-files	:= *.dtb *.dtbo
