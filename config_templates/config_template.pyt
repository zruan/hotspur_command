def configure_project(config):
    ##################################
    ##### Make your changes here #####
    ##################################
    # where to look for micrographs
    collection_dir = "{{ curr_dir }}/"
    # glob for micrograph scanning
    glob = "*/*.tif"
    # Scratch directory where data processing will be done. Should be an SSD
    scratch_dir = "/hotspur/scratch/{{ user }}/{{ curr_dir_base }}/"
    #Archive dir. If configured files will be moved there fore permanent storage
    archive_dir = "/tmp/JE_test_archive/"
    # Directory that holds lock files for processing
    lock_dir = "/hotspur/scratch/{{ user }}/{{ curr_dir_base }}/lock/"

    # edit values here to change them in all processes
    voltage = {{ voltage }}
    pixel_size_mc = {{ pixel_size_mc }}
    pixel_size_gctf = {{ pixel_size_gctf }}
    dose_rate = {{ dose_rate }}
    ac = {{ ac }}
    mc_para = '{{ mc_para }}'
    gctf_para = '{{ gctf_para }}'
    # you can add multiple GPUs here (e.g., [0,1]) to create multiple processes
    motioncor_gpus = [0]
    gctf_gpus = [0]

    ###############################################################
    ###### Don't edit below unless you know what you're doing #####
    ###############################################################

    ctffind_hereDoc = """ctffind << EOF
${stackname}_mc_DW.mrc
${scratch_dir}${filename_noex}_mc_DW_ctffind.ctf
${pixel_size_gctf} # pixelsize
${voltage} # acceleration voltage
2.70 # Cs
${ac} # amplitude contrast
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

    config.update({
        'collection_dir' : collection_dir,
        'glob' : glob,
        'scratch_dir' : scratch_dir,
        'archive_dir' : archive_dir,
        'lock_dir' : lock_dir,
        'voltage': voltage,
        'pixel_size_mc': pixel_size_mc,
        'pixel_size_gctf': pixel_size_gctf,
        'dose_rate': dose_rate,
        'ac': ac,
        'mc_para': mc_para,
        'gctf_para': gctf_para
    })

    if '.tif' in glob:
        config['moviestack'].update({
            "moviestack" : "${collection_dir}${base}.tif"
        })
        
    processes = []
    if '.tif' in glob:
        for gpu in motioncor_gpus:
            processes.append(CommandProcessor("motioncor2", "motioncor2 -InTiff ${filename} -OutMrc ${scratch_dir}${filename_noex}_mc.mrc -Kv ${voltage} -gain ref.mrc -PixSize ${pixel_size_mc} -FmDose ${dose_rate} ${mc_para} -Iter 10 -Tol 0.5 -Gpu " + str(gpu) + " > ${scratch_dir}${filename_noex}_mc.log; rm ${scratch_dir}${filename_noex}_mc.mrc", config, watch_glob=config["glob"], min_age=60, sleep=2, work_dir=config["collection_dir"], ensure_dirs=["${scratch_dir}${filename_directory}","${lock_dir}${filename_directory}"]))
    elif '.mrc' in glob:
        for gpu in motioncor_gpus:
            processes.append(CommandProcessor("motioncor2", "motioncor2 -InMrc ${filename} -OutMrc ${scratch_dir}${filename_noex}_mc.mrc -Kv ${voltage} -gain ref.mrc -PixSize ${pixel_size_mc} -FmDose ${dose_rate} ${mc_para} -Iter 10 -Tol 0.5 -Gpu " + str(gpu) + " > ${scratch_dir}${filename_noex}_mc.log; rm ${scratch_dir}${filename_noex}_mc.mrc", config, watch_glob=config["glob"], min_age=60, sleep=2, work_dir=config["collection_dir"], ensure_dirs=["${scratch_dir}${filename_directory}","${lock_dir}${filename_directory}"]))
    processes.append(PreviewProcessor("motioncor2_prev", config, "${stackname}_mc_DW.mrc", depends="motioncor2", min_age=0, sleep=2, work_dir=config["scratch_dir"]))
    for gpu in gctf_gpus:
        processes.append(CommandProcessor("gctf", "Gctf-v1.06_sm_30_cu8.0_x86_64 --apix ${pixel_size_gctf} --dstep 5 --kV ${voltage} --cs 2.7 --ac ${ac} --resH 4 --resL 20 --convsize 50 --defL 5000 --defH 50000 ${gctf_para} --gid " + str(gpu) + " --do_Hres_ref --do_EPA --do_validation --write_local_ctf 1 --logsuffix _gctf.log  --ctfstar ${stackname}_mc_DW_gctf.star ${stackname}_mc_DW.mrc > /dev/null", config, depends="motioncor2", min_age=0, sleep=2, work_dir=config["scratch_dir"]))
    processes.append(PreviewProcessor("gctf_prev", config, "${stackname}_mc_DW.ctf", depends="gctf", min_age=0, sleep=2, work_dir=config["scratch_dir"],suffix="_ctf",zoom=1.0))
    processes.append(CommandProcessor('ctffind', ctffind_hereDoc, config, depends="motioncor2", min_age=0, sleep=2, work_dir=config["scratch_dir"]))
    processes.append(PreviewProcessor('ctffind', config, "${stackname}_mc_DW_ctffind.ctf", depends = "ctffind", min_age = 0, sleep = 2, work_dir = config["scratch_dir"],suffix = '_ctffind', zoom=1.0))
    processes.append(CommandProcessor("montage", "( edmont -imin ${filename} -plout ${scratch_dir}${filename_noex}.plist.tmp -imout ${scratch_dir}${filename_noex}.mont.mrc.tmp && blendmont -imin ${scratch_dir}${filename_noex}.mont.mrc.tmp -imout ${scratch_dir}${filename_noex}.blend.mrc.tmp -plin ${scratch_dir}${filename_noex}.plist.tmp -roo tmp -bin 8 && mrc2tif -p ${scratch_dir}${filename_noex}.blend.mrc.tmp ${scratch_dir}${filename_noex}_preview.png && rm ${scratch_dir}${filename_noex}.*.tmp ) > ${scratch_dir}${filename_noex}.montage.log", config, watch_glob="grid*mm*.mrc", min_age=1800, sleep=2, work_dir=config["collection_dir"], ensure_dirs=["${scratch_dir}${filename_directory}","${lock_dir}${filename_directory}"]))
    processes.append(IdogpickerProcessor("idogpicker", config, "${stackname}_mc_DW.mrc", depends="motioncor2",min_age=0, sleep=2, work_dir=config["scratch_dir"]))

    return processes
