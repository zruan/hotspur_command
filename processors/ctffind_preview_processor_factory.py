from processors import PreviewProcessor

def get_gctf_prev_processor(config):
    return PreviewProcessor(
        'ctffind_prev',
        config,
        "${stackname}_mc_DW_ctffind.ctf",
        depends = "ctffind",
        min_age = 0,
        sleep = 2,
        work_dir=config["scratch_dir"],
        suffix='_ctf',
        zoom=1.0
    )