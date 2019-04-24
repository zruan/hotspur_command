from processors import PreviewProcessor

def get_gctf_prev_processor(config):
    return PreviewProcessor(
        "gctf_prev",
        config,
        "${stackname}_mc_DW.ctf",
        depends="gctf",
        min_age=0,
        sleep=2,
        work_dir=config["scratch_dir"],
        suffix="_ctf",
        zoom=1.0
    )
