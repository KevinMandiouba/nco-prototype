# Recreates the Vivado project inside build/.
# The glob checks are adapted from the BYU TclVivado wiki:
# https://github.com/byu-cpe/BYU-Computing-Tutorials/wiki/TclVivado

# ---- Config ----
set proj_name "nco_prototype"
set part      "xc7a35tcpg236-1"
set top_rtl   "nco"
set top_sim   "nco_tb"

# ---- Paths ----
set script_dir [file dirname [file normalize [info script]]]
set root_dir   [file dirname $script_dir]
set build_dir  [file join $root_dir build]

# ---- Project ----
close_project -quiet
# -force overwrites the old project
create_project $proj_name $build_dir -part $part -force
set_property target_language VHDL [current_project]

# ---- Sources ----
# copy files into build/
set rtl_files [glob -nocomplain -directory [file join $root_dir rtl] *.vhd */*.vhd]
if {[llength $rtl_files] > 0} {
    add_files $rtl_files
}

set tb_files [glob -nocomplain -directory [file join $root_dir tb] *.vhd */*.vhd]
if {[llength $tb_files] > 0} {
    add_files -fileset sim_1 $tb_files
}

set xdc_files [glob -nocomplain -directory [file join $root_dir constraints] *.xdc]
if {[llength $xdc_files] > 0} {
    add_files -fileset constrs_1 $xdc_files
}

# ---- Settings ----
set vhd_files [get_files -quiet *.vhd]
if {[llength $vhd_files] > 0} {
    set_property file_type {VHDL 2008} $vhd_files
}

# Tops are only set if the matching file exists (file name = entity name).
if {[lsearch -glob $rtl_files "*/$top_rtl.vhd"] >= 0} {
    set_property top $top_rtl [get_filesets sources_1]
} else {
    puts "Note: $top_rtl.vhd not found, Vivado will pick the synthesis top"
}

if {[lsearch -glob $tb_files "*/$top_sim.vhd"] >= 0} {
    set_property top $top_sim [get_filesets sim_1]
} else {
    puts "Note: $top_sim.vhd not found, Vivado will pick the simulation top"
}

if {[llength $rtl_files] > 0} {
    update_compile_order -fileset sources_1
}
if {[llength $tb_files] > 0} {
    update_compile_order -fileset sim_1
}

puts "Project created: [file join $build_dir $proj_name.xpr]"