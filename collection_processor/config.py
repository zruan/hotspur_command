
config = {
        # Directory that will be scanned for micrographs
        "collection_dir" : "${curr_dir}/",
        # Glob that will be used to scan for new mrc files
        "glob" : "*/stack_????.mrc",
        # Scratch directo where data processing will be done. Should be an SSD
        "scratch_dir" : "/home/scratch/${user}/${curr_dir_base}/",
        # Archive dir. If configured files will be moved there fore permanent storage
        "archive_dir" : "/tmp/JE_test_archive/",
        # Directory that holds lock files for processing
        "lock_dir"    : "/home/scratch/${user}/${curr_dir_base}/lock/",
        "parser" :{ "MotionCor2Parser" : {
		"watch_file" : "$${lock_dir}$${base}.motioncor2.done",
                "sum_micrograph_glob" : "$${base}_mc.mrc",
                "dw_micrograph_glob" : "$${base}_mc_DW.mrc",
                "log_glob" : "$${base}_mc.log",
                "preview_glob" : "$${base}_mc_DW.preview.png"
                },
           "GctfParser" : {
		"watch_file" : "$${lock_dir}$${base}.gctf.done",
                "ctf_image_glob" : "$${base}_mc_DW.ctf",
                "ctf_image_preview_glob" : "$${base}_mc_DW_ctf.preview.png",
                "ctf_star_glob" : "$${base}_mwc_DW_gctf.star",
                "ctf_epa_log_glob" : "$${base}_mc_DW_EPA.log",
                "ctf_log_glob" : "$${base}_mc_DW_gctf.log"
                },
           "StackParser" : {
               "glob" : "*/stack_????_gain.mrc"
               },
	   "Database" : "data.json"
         }
        }

processes = [
CommandProcessor("clip", "/eppec/storage/sw/imod/4.8.58/bin/clip mult -m 2 -D defects.txt $${filename} ref.mrc $${scratch_dir}$${filename_noex}_gain.mrc > $${scratch_dir}$${filename_noex}_clip.log ",config, watch_glob= config["glob"], min_age=5, sleep=2, work_dir=config["collection_dir"], ensure_dirs=["$${scratch_dir}$${filename_directory}","$${lock_dir}$${filename_directory}"]),
CommandProcessor("motioncor2", "/eppec/storage/sw/motioncor2/20161019/motioncor2 -InMrc $${stackname}_gain.mrc -OutMrc $${stackname}_mc.mrc -Kv 300 -PixSize 1.7 -FmDose 1.0 -Iter 10 -Tol 0.5 -Gpu 0 > $${stackname}_mc.log ", config, depends="clip", min_age=0, sleep=2, work_dir=config["scratch_dir"]),
PreviewProcessor("motioncor2_prev", config, "$${stackname}_mc_DW.mrc", depends="motioncor2", min_age=0, sleep=2, work_dir=config["scratch_dir"]),
CommandProcessor("gctf", "/eppec/storage/sw/gctf/1.06/bin/Gctf-v1.06_sm_30_cu8.0_x86_64 --apix 1.7 --kV 300 --cs 2.7 --ac 0.01 --resH 4 --resL 20 --convsize 50 --defL 5000 --defH 50000 --do_Hres_ref --do_EPA --do_validation --phase_shift_L 30 --phase_shift_H 140 --phase_shift_S 5 --write_local_ctf 1 --logsuffix _gctf.log  --ctfstar $${stackname}_mc_DW_gctf.star $${stackname}_mc_DW.mrc > /dev/null", config, depends="motioncor2", min_age=0, sleep=2, work_dir=config["scratch_dir"]),
PreviewProcessor("gctf_prev", config, "$${stackname}_mc_DW.ctf", depends="gctf", min_age=0, sleep=2, work_dir=config["scratch_dir"],suffix="_ctf",zoom=1.0)
]
