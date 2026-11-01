SIM = ghdl
TOPLEVEL_LANG = vhdl
TOPLEVEL = NCO

VHDL_SOURCES = $(abspath ../../rtl/nco/sine_rom_pkg.vhd)
VHDL_SOURCES += $(abspath ../../rtl/nco/nco.vhd)

COCOTB_TEST_MODULES = test_nco

COMPILE_ARGS += --std=08
SIM_ARGS += --wave=nco.ghw

include $(shell cocotb-config --makefiles)/Makefile.sim