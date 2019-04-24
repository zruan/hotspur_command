from processors import CommandProcessor
from functools import partial

command = """ motioncor2 << EOF
${filetype_flag} ${filename}
-OutMrc ${scratch_dir}${filename_noex}_mc.mrc
-Kv ${voltage}
-gain ${gain_ref}
-PixSize ${pixel_size_mc}
-FmDose ${dose_rate} ${mc_para}
-Iter 10
-Tol 0.5 -Gpu ${gpu} > ${scratch_dir}${filename_noex}_mc.log;
rm ${scratch_dir}${filename_noex}_mc.mrc"
EOF"""

def get_motioncor2_processor(config):
    if config['filetype'] == 'tif':
        filetype_flag = '-InTiff'
    else:
        filetype_flag = '-InMrc'
    updated_command = partial(command.format, filetype_flag=filetype_flag)
    return CommandProcessor(
        'motioncor2',
        updated_command,
        config,
        watch_glob=config["glob"],
        min_age=60,
        sleep=2,
        work_dir=config["collection_dir"],
        ensure_dirs=["${scratch_dir}${filename_directory}","${lock_dir}${filename_directory}"]
    )