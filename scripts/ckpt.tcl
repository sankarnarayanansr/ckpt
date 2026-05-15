# Vivado TCL integration for ckpt
# Source this in your Vivado TCL console or add to your project TCL script:
#   source scripts/ckpt.tcl
#
# Then use:
#   ckpt_save "after synthesis"
#   ckpt_list
#   ckpt_restore 9e1b3ac

proc ckpt_save { message } {
    set cmd "ckpt save \"$message\""
    puts "==> $cmd"
    exec sh -c $cmd >@stdout 2>@stderr
}

proc ckpt_list {} {
    exec sh -c "ckpt list" >@stdout 2>@stderr
}

proc ckpt_restore { id } {
    set cmd "ckpt restore $id"
    puts "==> $cmd"
    exec sh -c $cmd >@stdout 2>@stderr
}

# Auto-save hook — call after key run steps
proc ckpt_after_synth {} {
    ckpt_save "post-synthesis [clock format [clock seconds] -format {%Y%m%d-%H%M}]"
}

proc ckpt_after_impl {} {
    ckpt_save "post-implementation [clock format [clock seconds] -format {%Y%m%d-%H%M}]"
}

puts "ckpt TCL integration loaded. Commands: ckpt_save, ckpt_list, ckpt_restore"
