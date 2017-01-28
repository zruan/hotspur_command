
config = {
        # Directory that will be scanned for micrographs
        "collection_dir" : "${curr_dir}/",
        # Glob that will be used to scan for new mrc files
        "glob" : "*/stack_????.mrc",
        # Scratch directo where data processing will be done. Should be an SSD
        "scratch_dir" : "/scratch/${user}/${curr_dir_base}/",
        # Archive dir. If configured files will be moved there fore permanent storage
        "archive_dir" : "/tmp/JE_test_archive/",
        # Directory that holds lock files for processing
        "lock_dir"    : "/scratch/${user}/${curr_dir_base}/lock/",
        "parser" :{ "MotionCor2" : {
		"type" : MotionCor2Parser,
		"depends" : "motioncor2",
                "sum_micrograph" : "$${base}_mc.mrc",
                "dw_micrograph" : "$${base}_mc_DW.mrc",
                "log" : "$${base}_mc.log",
                "preview" : "$${base}_mc_DW.preview.png"
                },
           "Gctf" : {
		"type" : GctfParser,
		"depends" : "gctf",
                "ctf_image" : "$${base}_mc_DW.ctf",
                "ctf_image_preview" : "$${base}_mc_DW_ctf.preview.png",
                "ctf_star" : "$${base}_mwc_DW_gctf.star",
                "ctf_epa_log" : "$${base}_mc_DW_EPA.log",
                "ctf_log" : "$${base}_mc_DW_gctf.log"
                },
           "moviestack" : {
               "type": StackParser,
               "depends" : "motioncor2",
               "moviestack" : "$${collection_dir}$${base}.mrc"
               },
      "Database" : "data.json"
         }
        }

processes = [
CommandProcessor("motioncor2", "/eppec/storage/sw/motioncor2/20161019/motioncor2 -InMrc $${filename} -OutMrc $${scratch_dir}$${filename_noex}_mc.mrc -Kv 300 -gain ref.mrc -PixSize 1.7 -FmDose 1.0 -Iter 10 -Tol 0.5 -Gpu 0 > $${scratch_dir}$${filename_noex}_mc.log", config, watch_glob=config["glob"], min_age=5, sleep=2, work_dir=config["collection_dir"], ensure_dirs=["$${scratch_dir}$${filename_directory}","$${lock_dir}$${filename_directory}"]),
PreviewProcessor("motioncor2_prev", config, "$${stackname}_mc_DW.mrc", depends="motioncor2", min_age=0, sleep=2, work_dir=config["scratch_dir"]),
CommandProcessor("gctf", "/eppec/storage/sw/gctf/1.06/bin/Gctf-v1.06_sm_30_cu8.0_x86_64 --apix 1.7 --kV 300 --cs 2.7 --ac 0.01 --resH 4 --resL 20 --convsize 50 --defL 5000 --defH 50000 --do_Hres_ref --do_EPA --do_validation --phase_shift_L 30 --phase_shift_H 140 --phase_shift_S 5 --write_local_ctf 1 --logsuffix _gctf.log  --ctfstar $${stackname}_mc_DW_gctf.star $${stackname}_mc_DW.mrc > /dev/null", config, depends="motioncor2", min_age=0, sleep=2, work_dir=config["scratch_dir"]),
PreviewProcessor("gctf_prev", config, "$${stackname}_mc_DW.ctf", depends="gctf", min_age=0, sleep=2, work_dir=config["scratch_dir"],suffix="_ctf",zoom=1.0)
]
