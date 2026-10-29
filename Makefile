vendor := $(srctree)/$(src)

# The TB520FU kernel (CONFIG_ARCH_LAPIS) only builds the lapis dtbs: the
# Qualcomm boards of qcom/ would otherwise be merged into the dtb image too.
ifneq "$(CONFIG_ARCH_LAPIS)" "y"
ifneq "$(wildcard $(vendor)/qcom)" ""
	subdir-y += qcom
endif
endif

ifneq "$(wildcard $(vendor)/lenovo)" ""
	subdir-y += lenovo
endif
