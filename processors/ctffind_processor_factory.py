from processors import CommandProcessor

command = """ctffind << EOF
${stackname}_mc_DW.mrc
${scratch_dir}${filename_noex}_mc_DW_ctffind.ctf
${pixel_size_gctf} # pixelsize
${voltage} # acceleration voltage
2.70 # Cs
0.1 # amplitude contrast
512 # size of amplitude spectrum to compute
20 # min resolution
4 # max resolution
5000 # min defocus
50000 # max defoxus
500 # defocus search step
no # is astig known
yes # slower, more exhaustive search
yes # use a restraint on astig
200.0 # expected (tolerated) astig
no # find additional phase shift
no # set expert options
EOF"""

def get_ctffind_processor(config):
    return CommandProcessor(
        'ctffind',
        command,
        config,
        depends="motioncor2",
        min_age=0,
        sleep=2,
        work_dir=config["scratch_dir"]
    )