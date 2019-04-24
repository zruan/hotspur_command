from processors import CommandProcessor

command = """ Gctf-v1.06_sm_30_cu8.0_x86_64 << EOF
--apix ${pixel_size_gctf}
--dstep 5
--kV ${voltage}
--cs 2.7 
--ac ${ac}
--resH 4
--resL 20
--convsize 50
--defL 5000
--defH 50000 ${gctf_para}
--gid " + str(gpu) + "
--do_Hres_ref
--do_EPA
--do_validation
--write_local_ctf 1
--logsuffix _gctf.log
--ctfstar ${stackname}_mc_DW_gctf.star ${stackname}_mc_DW.mrc
> /dev/null"
EOF"""

def get_gctf_processor(config):
    return CommandProcessor(
        'gctf',
        command,
        config,
        depends="motioncor2",
        min_age=0,
        sleep=2,
        work_dir=config["scratch_dir"]
    )