import os

from hotspur_utils import couchdb_utils
from data_models import SessionData, AcquisitionData, MotionCorrectionData, CtfData

class Micrograph():
    def __init__(self, acquisition_data=None, motion_correction_data=None, ctf_data=None):
        self.acquisition_data = acquisition_data
        self.motion_correction_data = motion_correction_data
        self.ctf_data = ctf_data

def export(args):
    db = couchdb_utils.fetch_db(args.hash)
    session = SessionData()
    session.fetch(db)

    acquisition_data = AcquisitionData.fetch_all(db)
    motion_correction_data = MotionCorrectionData.fetch_all(db)
    ctf_data = CtfData.fetch_all(db)

    micrographs = {}

    for data in acquisition_data:
        micrograph = Micrograph()
        micrograph.acquisition_data = data
        micrographs[data.base_name] = micrograph

    for data in motion_correction_data:
        micrograph = micrographs[data.base_name]
        micrograph.motion_correction_data = data

    for data in ctf_data:
        micrograph = micrographs[data.base_name]
        micrograph.ctf_data = data

    micrographs = micrographs.values()
    
    if args.out_dir is not None:
        out_base = args.out_dir
    else:
        out_base = session.processing_directory
    out_base = os.path.abspath(out_base)
    out_dir = f"{out_base}/hotspur-export"
    os.makedirs(out_dir, exist_ok=True)

    star_string = generate_movie_star(micrographs)
    with open(f'{out_dir}/movies.star', 'w') as fp:
        fp.write(star_string)

    meta_out_dir = f'{out_dir}/motioncor_meta'
    for micrograph in micrographs:
        os.makedirs(meta_out_dir, exist_ok=True)
        star_string = generate_motion_metadata_star(micrograph)
        path = f'{meta_out_dir}/{micrograph.motion_correction_data.base_name}.star'
        with open(path, 'w') as fp:
            fp.write(star_string)

    star_string = generate_motion_correction_star(micrographs, meta_out_dir)
    with open(f'{out_dir}/corrected_micrographs.star', 'w') as fp:
        fp.write(star_string)

    # star_string = generate_ctf_star(micrographs)
    # with open(f'{out_dir}/micrographs_ctf.star', 'w') as fp:
    #     fp.write(star_string)

    print(f"Exported project to {out_dir}")


def generate_movie_star(micrographs):
    star_string = '\n'.join([
        "data_",
        "loop_",
        "_rlnMicrographMovieName",
        ""
    ])
    micrograph_paths = [micrograph.acquisition_data.image_path for micrograph in micrographs]
    star_string += '\n'.join(micrograph_paths)
    return star_string

def generate_motion_metadata_star(micrograph):
    ad = micrograph.acquisition_data
    mcd = micrograph.motion_correction_data

    out_string = '\n'.join([
        "data_general",
        "",
        f"_rlnImageSizeX                      {mcd.dimensions[0]}",
        f"_rlnImageSizeY                      {mcd.dimensions[1]}",
        f"_rlnImageSizeZ                      {ad.frame_count}",
        f"_rlnMicrographMovieName             {mcd.corrected_image_file}",
        f"_rlnMicrographBinning               {mcd.binning}",
        f"_rlnMicrographOriginalPixelSize     {ad.pixel_size}",
        f"_rlnMicrographDoseRate              {ad.frame_dose}",
        "_rlnMicrographPreExposure            0.000000",
        f"_rlnVoltage                         {ad.voltage}",
        "_rlnMicrographStartFrame             1",
        "_rlnMotionModelVersion               0",
        "",
        "",
        "data_global_shift",
        "",
        "loop_",
        "_rlnMicrographFrameNumber #1",
        "_rlnMicrographShiftX      #2",
        "_rlnMicrographShiftY      #3",
        ""
    ])
    shifts = [f"{i} {shift[0]} {shift[1]}" for i, shift in enumerate(mcd.displacement_list)]
    out_string += '\n'.join(shifts)
    return out_string

def generate_motion_correction_star(micrographs, meta_out_dir):
    out_string = '\n'.join([
        "data_",
        "loop_",
        "_rlnMicrographName     #1",
        "_rlnMicrographMetadata #2",
        "_rlnAccumMotionTotal   #3",
        "_rlnAccumMotionEarly   #4",
        "_rlnAccumMotionLate    #5",
        ""
    ])
    rows = []
    for mcd in [micrograph.motion_correction_data for micrograph in micrographs]:
        row = ' '.join([
            f'{mcd.corrected_image_file}',
            f'{meta_out_dir}/{mcd.base_name}.star',
            f'{mcd.total_accumulated_distance}',
            f'{mcd.early_accumulated_distance}',
            f'{mcd.late_accumulated_distance}'
        ])
        rows.append(row)
    out_string += '\n'.join(rows)
    return out_string

# def generate_ctf_star(micrographs):
#     out_string = '\n'.join([
#         '# RELION; version 3.0.5',
#         '',
#         'data_',
#         '',
#         'loop_',
#         '_rlnMicrographName      #1',
#         '_rlnCtfImage            #2',
#         '_rlnDefocusU            #3',
#         '_rlnDefocusV            #4',
#         '_rlnCtfAstigmatism      #5',
#         '_rlnDefocusAngle        #6',
#         '_rlnVoltage             #7',
#         '_rlnSphericalAberration #8',
#         '_rlnAmplitudeContrast   #9',
#         '_rlnMagnification       #10',
#         '_rlnDetectorPixelSize   #11',
#         '_rlnCtfFigureOfMerit    #12',
#         '_rlnCtfMaxResolution    #13',
#     ])
#     rows = []
#     for mcd, cd in [(micrograph.motion_correction_data, micrograph.ctf_data) for micrograph in micrographs]:
#         row = ' '.join([
#             f'{mcd.aligned_image_file}',
#             f'{meta_out_dir}/{mcd.base_name}',
#             f'{mcd.total_shift}',
#             f'{mcd.initial_shift}',
#             f'{mcd.initial_shift}'
#         ])
#         rows.append(row)
#     return out_string