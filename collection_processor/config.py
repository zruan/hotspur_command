
config = {
        # Directory that will be scanned for micrographs
        "collection_dir" : "${curr_dir}/",
        # Glob that will be used to scn for new mrc files
        "glob" : "*/stack_????.mrc",
        # Scratch directo where data processing will be done. Should be an SSD
        "scratch_dir" : "/home/scratch/${user}/${curr_dir_base}/",
        # Archive dir. If configured files will be moved there fore permanent storage
        "archive_dir" : "/tmp/JE_test_archive/",
        # Directory that holds lock files for processing
        "lock_dir"    : "/home/scratch/${user}/${curr_dir_base}/lock/",
        "parser" : { 
                "Database" : "data.json":,
                "MotionCor2Parser" : {
                "sum_micrograph_glob" : "${base}_mc.mrc",
                "dw_micrograph_glob" : "${base}_mc_DW.mrc",
                "log_glob" : "${base}_mc.log"
                },
           "PreviewParser" : {
                "image_glob" : "${base}_mc_prev.preview.png"
                },
           "GctfParser" : {
                "ctf_image_glob" : "${base}_mc_DW_ctf.mrc",
                "ctf_image_preview_glob" : "${base}_mc_DW_ctf_prev.preview.png",
                "ctf_star_glob" : "${base}_mwc_DW_gctf.star",
                "ctf_epa_log_glob" : "${base}_mc_DW_EPA.log",
                "ctf_log_glob" : "${base}_mc_DW_gctf.log"
                }
         }
        }

processes = [
CommandProcessor("clip", "/eppec/storage/sw/imod/4.8.58/bin/clip mult -m 2 -D defects.txt $${filename} ref.mrc $${scratch_dir}$${filename_noex}_gain.mrc > $${scratch_dir}$${filename_noex}_clip.log ", config["glob"], config, min_age=5, sleep=5, work_dir=config["collection_dir"], ensure_dirs=["$${scratch_dir}$${filename_directory}","$${lock_dir}$${filename_directory}"]),
CommandProcessor("motioncor2", "/eppec/storage/sw/motioncor2/20161019/motioncor2 -InMrc $${filename} -OutMrc $${filename_noex}_mc.mrc -Kv 300 -PixSize 1.7 -FmDose 1.0 -Iter 10 -Tol 0.5 -Gpu 0 > $${filename_noex}_mc.log ", pyfs.rext(config["glob"])+".mrc.clip.done", config, min_age=1, sleep=5, work_dir=config["scratch_dir"], done_lambda = lambda x: pyfs.rext(x, full=True)+"_gain.mrc"),
PreviewProcessor("motioncor2_prev", pyfs.rext(config["glob"])+"_gain_mc_DW.mrc", config, min_age=5, sleep=5, work_dir=config["scratch_dir"]),
CommandProcessor("gctf", "/eppec/storage/sw/gctf/1.06/bin/Gctf-v1.06_sm_30_cu8.0_x86_64 --apix 1.7 --kV 300 --cs 2.7 --ac 0.01 --resH 4 --resL 20 --convsize 50 --defL 5000 --defH 50000 --do_Hres_ref --do_EPA --do_validation --phase_shift_L 30 --phase_shift_H 140 --phase_shift_S 5 --write_local_ctf 1 --logsuffix _gctf.log  --ctfstar $${filename_noex}_gctf.star $${filename} > /dev/null", pyfs.rext(config["glob"])+"_gain.mrc.motioncor2.done", config, min_age=1, sleep=5, work_dir=config["scratch_dir"], done_lambda = lambda x: pyfs.rext(x, full=True)+"_mc_DW.mrc"),
PreviewProcessor("gctf_prev", pyfs.rext(config["glob"])+"_gain_mc_DW.ctf", config, min_age=5, sleep=5, work_dir=config["scratch_dir"]),
]
