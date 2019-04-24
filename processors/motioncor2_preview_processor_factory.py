from processors import PreviewProcessor

def get_motioncor2_prev_processor(config):
    return PreviewProcessor(
        "motioncor2_prev",
        config,
        "${stackname}_mc_DW.mrc",
        depends="motioncor2",
        min_age=0,
        sleep=2,
        work_dir=config["scratch_dir"]
    )
