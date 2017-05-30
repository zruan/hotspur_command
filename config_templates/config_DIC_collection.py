
config = {
        # Directory that will be scanned for micrographs
        "collection_dir" : "${curr_dir}/",
        # Glob that will be used to scan for new mrc files
        "glob" : "*/*.mrc",
        # Scratch directo where data processing will be done. Should be an SSD
        "scratch_dir" : "/hotspur/scratch/${user}/${curr_dir_base}/",
        # Archive dir. If configured files will be moved there fore permanent storage
        "archive_dir" : "/tmp/JE_test_archive/",
        # Directory that holds lock files for processing
        "lock_dir"    : "/hotspur/scratch/${user}/${curr_dir_base}/lock/",
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
	       "depends" : "clip",
	       "moviestack" : "$${base}_gain.mrc"
               },
	   "Database" : "data.json"
         }
        }

processes = [
CommandProcessor("clip", "/eppec/storage/sw/imod/4.8.58/bin/clip unpack -D defects.txt $${filename} ref.mrc $${scratch_dir}$${filename_noex}_gain.mrc > $${scratch_dir}$${filename_noex}_clip.log ",config, watch_glob= config["glob"], min_age=60, sleep=2, work_dir=config["collection_dir"], ensure_dirs=["$${scratch_dir}$${filename_directory}","$${lock_dir}$${filename_directory}"]),
CommandProcessor("motioncor2", "/eppec/storage/sw/motioncor2/20161019/motioncor2 -InMrc $${stackname}_gain.mrc -OutMrc $${stackname}_mc.mrc -Patch 5 5 -Kv 300 -FtBin 2 -PixSize 0.85 -FmDose 1.0 -Iter 10 -Tol 0.5 -Gpu 0 > $${stackname}_mc.log ", config, depends="clip", min_age=0, sleep=2, work_dir=config["scratch_dir"]),
CommandProcessor("motioncor2", "/eppec/storage/sw/motioncor2/20161019/motioncor2 -InMrc $${stackname}_gain.mrc -OutMrc $${stackname}_mc.mrc -Patch 5 5 -Kv 300 -FtBin 2 -PixSize 0.85 -FmDose 1.0 -Iter 10 -Tol 0.5 -Gpu 1 > $${stackname}_mc.log ", config, depends="clip", min_age=0, sleep=2, work_dir=config["scratch_dir"]),
PreviewProcessor("motioncor2_prev", config, "$${stackname}_mc_DW.mrc", depends="motioncor2", min_age=0, sleep=2, work_dir=config["scratch_dir"]),
CommandProcessor("gctf", "/eppec/storage/sw/gctf/1.06/bin/Gctf-v1.06_sm_30_cu8.0_x86_64 --apix 1.7 --kV 300 --cs 2.7 --ac 0.01 --resH 4 --resL 20 --convsize 50 --defL 5000 --defH 50000 --do_Hres_ref --do_EPA --do_validation --write_local_ctf 1 --logsuffix _gctf.log  --ctfstar $${stackname}_mc_DW_gctf.star $${stackname}_mc_DW.mrc > /dev/null", config, depends="motioncor2", min_age=0, sleep=2, work_dir=config["scratch_dir"]),
PreviewProcessor("gctf_prev", config, "$${stackname}_mc_DW.ctf", depends="gctf", min_age=0, sleep=2, work_dir=config["scratch_dir"],suffix="_ctf",zoom=1.0)
]
