
config = {
        # Directory that will be scanned for micrographs
        "collection_dir" : "{{curr_dir}}/",
        # Glob that will be used to scan for new mrc files
        "glob" : "*/*.mrc",
        # Scratch directo where data processing will be done. Should be an SSD
        "scratch_dir" : "/hotspur/scratch/{{user}}/{{curr_dir_base}}/",
        # Archive dir. If configured files will be moved there fore permanent storage
        "archive_dir" : "/tmp/JE_test_archive/",
        # Directory that holds lock files for processing
        "lock_dir"    : "/hotspur/scratch/{{user}}/{{curr_dir_base}}/lock/",
        "parser" :{ "MotionCor2" : {
		"type" : MotionCor2Parser,
		"depends" : "motioncor2",
                "sum_micrograph" : "${base}_mc.mrc",
                "dw_micrograph" : "${base}_mc_DW.mrc",
                "log" : "${base}_mc.log",
                "preview" : "${base}_mc_DW.preview.png"
                },
           "Gctf" : {
		"type" : GctfParser,
		"depends" : "gctf",
                "ctf_image" : "${base}_mc_DW.ctf",
                "ctf_image_preview" : "${base}_mc_DW_ctf.preview.png",
                "ctf_star" : "${base}_mwc_DW_gctf.star",
                "ctf_epa_log" : "${base}_mc_DW_EPA.log",
                "ctf_log" : "${base}_mc_DW_gctf.log"
                },
           "moviestack" : {
               "type": StackParser,
               "depends" : "motioncor2",
               "moviestack" : "${collection_dir}${base}.mrc"
               },
           "navigator" : {
               "type": NavigatorParser,
               "glob" : "${collection_dir}*.nav",
               "stackname_lambda" : lambda x, config : pyfs.rext(x[len(config["collection_dir"]):],full=True),
               "navigatorfile" : "${collection_dir}${base}.nav"
               },
           "montage" : {
               "type": MontageParser,
               "glob" : "${lock_dir}/*.montage.done",
               "stackname_lambda" : lambda x, config : pyfs.rext(x[len(config["lock_dir"]):],full=True),
               "montage" : "${collection_dir}${base}.mrc"
               },
      "Database" : "data.json"
         }
        }

processes = [
CommandProcessor("motioncor2", "motioncor2 -InMrc ${filename} -OutMrc ${scratch_dir}${filename_noex}_mc.mrc -Kv 300 -gain ref.mrc -PixSize {{ pixel_size_mc }} -FmDose {{ dose_rate }} {{ mc_para }} -Iter 10 -Tol 0.5 -Gpu 0 > ${scratch_dir}${filename_noex}_mc.log", config, watch_glob=config["glob"], min_age=60, sleep=2, work_dir=config["collection_dir"], ensure_dirs=["${scratch_dir}${filename_directory}","${lock_dir}${filename_directory}"]),
PreviewProcessor("motioncor2_prev", config, "${stackname}_mc_DW.mrc", depends="motioncor2", min_age=0, sleep=2, work_dir=config["scratch_dir"]),
CommandProcessor("gctf", "Gctf-v1.06_sm_30_cu8.0_x86_64 --apix {{ pixel_size_gctf }} --dstep 5 --kV 300 --cs 2.7 --ac {{ ac }} --resH 4 --resL 20 --convsize 50 --defL 5000 --defH 50000 {{ gctf_para }} --do_Hres_ref --do_EPA --do_validation --write_local_ctf 1 --logsuffix _gctf.log  --ctfstar ${stackname}_mc_DW_gctf.star ${stackname}_mc_DW.mrc > /dev/null", config, depends="motioncor2", min_age=0, sleep=2, work_dir=config["scratch_dir"]),
PreviewProcessor("gctf_prev", config, "${stackname}_mc_DW.ctf", depends="gctf", min_age=0, sleep=2, work_dir=config["scratch_dir"],suffix="_ctf",zoom=1.0),
CommandProcessor("montage", "( edmont -imin ${filename} -plout ${scratch_dir}${filename_noex}.plist.tmp -imout ${scratch_dir}${filename_noex}.mont.mrc.tmp && blendmont -imin ${scratch_dir}${filename_noex}.mont.mrc.tmp -imout ${scratch_dir}${filename_noex}.blend.mrc.tmp -plin ${scratch_dir}${filename_noex}.plist.tmp -roo tmp -bin 8 && mrc2tif -p ${scratch_dir}${filename_noex}.blend.mrc.tmp ${scratch_dir}${filename_noex}_preview.png && rm ${scratch_dir}${filename_noex}.*.tmp ) > ${scratch_dir}${filename_noex}.montage.log", config, watch_glob="grid*mm*.mrc", min_age=1800, sleep=2, work_dir=config["collection_dir"], ensure_dirs=["${scratch_dir}${filename_directory}","${lock_dir}${filename_directory}"]),
]
