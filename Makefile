vendor := $(srctree)/$(src)

ifneq "$(wildcard $(vendor)/qcom)" ""
	subdir-y += qcom
endif

ifneq "$(wildcard $(vendor)/lenovo)" ""
	subdir-y += lenovo
endif
