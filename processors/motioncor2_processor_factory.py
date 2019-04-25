from processors import CommandProcessor

def get_motioncor2_processor(config):
    command_list = [
        'motioncor2',
        '-InTiff' if config['filetype'] == 'tif' else '-InMrc',
        '${collection_dir}${filename}',
        '-OutMrc ${scratch_dir}${filename_noex}_mc.mrc',
        '-Kv ${voltage}',
        '-gain ${gain_ref}',
        '-PixSize ${pixel_size}',
        '-FmDose ${frame_dose}',
        '-FtBin 2' if config['binning'] == 0.5 else '',
        '-Iter 10',
        '-Tol 0.5 -Gpu 0',
        '> ${scratch_dir}${filename_noex}_mc.log',
        '&& mv ${scratch_dir}${filename_noex}_mc.mrc ${scratch_dir}${filename_noex}_mc_DW.mrc'
    ]

    print('WARNING: dose weighted images are being overwritten by non-dose weighted images.')

    command = ' '.join(command_list)

    config['glob'] = '*.tif' if config['filetype'] == 'tif' else '*.mrc'
    
    return CommandProcessor(
        'motioncor2',
        command,
        config,
        watch_glob=config['glob'],
        min_age=60,
        sleep=2,
        work_dir=config['frames_directory'],
        ensure_dirs=['${scratch_dir}${filename_directory}', '${lock_dir}${filename_directory}']
   )