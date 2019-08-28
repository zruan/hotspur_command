import os
import tempfile

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

    export_dir_suffix = 'hotspur-export'
    frame_dir_suffix = f'{export_dir_suffix}/frames'
    mc_dir_suffix = f'{export_dir_suffix}/motioncor2'
    ctf_dir_suffix = f'{export_dir_suffix}/ctffind'

    export_dir = f"{out_base}/{export_dir_suffix}"
    frame_dir = f'{out_base}/{frame_dir_suffix}'
    mc_dir = f'{out_base}/{mc_dir_suffix}'
    ctf_dir = f'{out_base}/{ctf_dir_suffix}'

    os.makedirs(export_dir, exist_ok=True)
    os.makedirs(frame_dir, exist_ok=True)
    os.makedirs(mc_dir, exist_ok=True)
    os.makedirs(ctf_dir, exist_ok=True)

    for ad in [mg.acquisition_data for mg in micrographs]:
        ad.image_link_path = f'{frame_dir_suffix}/{os.path.basename(ad.image_path)}'
        link_target = f'{out_base}/{ad.image_link_path}'
        symlink(ad.image_path, link_target, overwrite=True)

    star_string = generate_movie_star(micrographs)
    with open(f'{export_dir}/movies.star', 'w') as fp:
        fp.write(star_string)

    for mcd in [mg.motion_correction_data for mg in micrographs]:
        mcd.image_link_path = f'{mc_dir_suffix}/{os.path.basename(mcd.corrected_image_file)}'
        link_target = f'{out_base}/{mcd.image_link_path}'
        symlink(mcd.corrected_image_file, link_target, overwrite=True)

    for micrograph in micrographs:
        star_string = generate_motion_metadata_star(micrograph)
        mcd = micrograph.motion_correction_data
        mcd.metadata_file = f'{mc_dir_suffix}/{mcd.base_name}.star'
        full_path = f'{out_base}/{mcd.metadata_file}'
        with open(full_path, 'w') as fp:
            fp.write(star_string)

    star_string = generate_motion_correction_star(micrographs)
    with open(f'{export_dir}/corrected_micrographs.star', 'w') as fp:
        fp.write(star_string)

    for cd in [mg.ctf_data for mg in micrographs]:
        cd.image_link_path = f'{ctf_dir_suffix}/{os.path.basename(cd.ctf_image_file)}'
        link_target = f'{out_base}/{cd.image_link_path}'
        symlink(cd.ctf_image_file, link_target, overwrite=True)

    star_string = generate_ctf_star(micrographs)
    with open(f'{export_dir}/micrographs_ctf.star', 'w') as fp:
        fp.write(star_string)

    print(f"Exported project to {export_dir}")


def generate_movie_star(micrographs):
    star_string = '\n'.join([
        "data_",
        "loop_",
        "_rlnMicrographMovieName",
        ""
    ])
    micrograph_paths = [micrograph.acquisition_data.image_link_path for micrograph in micrographs]
    star_string += '\n'.join(micrograph_paths)
    return star_string

def generate_motion_metadata_star(micrograph):
    ad = micrograph.acquisition_data
    mcd = micrograph.motion_correction_data

    out_string = '\n'.join([
        f"data_general",
        f"",
        f"_rlnImageSizeX                      {mcd.dimensions[0]}",
        f"_rlnImageSizeY                      {mcd.dimensions[1]}",
        f"_rlnImageSizeZ                      {ad.frame_count}",
        f"_rlnMicrographMovieName             {mcd.image_link_path}",
        f"_rlnMicrographBinning               {mcd.binning}",
        f"_rlnMicrographOriginalPixelSize     {ad.pixel_size}",
        f"_rlnMicrographDoseRate              {ad.frame_dose}",
        f"_rlnMicrographPreExposure           0.000000",
        f"_rlnVoltage                         {ad.voltage}",
        f"_rlnMicrographStartFrame            1",
        f"_rlnMotionModelVersion              0",
        f"",
        f"",
        f"data_global_shift",
        f"",
        f"loop_",
        f"_rlnMicrographFrameNumber #1",
        f"_rlnMicrographShiftX      #2",
        f"_rlnMicrographShiftY      #3",
        f""
    ])
    shifts = [f"{i} {shift[0]} {shift[1]}" for i, shift in enumerate(mcd.displacement_list)]
    out_string += '\n'.join(shifts)
    return out_string

def generate_motion_correction_star(micrographs):
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
            f'{mcd.image_link_path}',
            f'{mcd.metadata_file}',
            f'{mcd.total_accumulated_distance}',
            f'{mcd.early_accumulated_distance}',
            f'{mcd.late_accumulated_distance}'
        ])
        rows.append(row)
    out_string += '\n'.join(rows)
    return out_string

def generate_ctf_star(micrographs):
    out_string = '\n'.join([
        '# RELION; version 3.0.5',
        '',
        'data_',
        '',
        'loop_',
        '_rlnMicrographName      #1',
        '_rlnCtfImage            #2',
        '_rlnDefocusU            #3',
        '_rlnDefocusV            #4',
        '_rlnCtfAstigmatism      #5',
        '_rlnDefocusAngle        #6',
        '_rlnVoltage             #7',
        '_rlnSphericalAberration #8',
        '_rlnAmplitudeContrast   #9',
        '_rlnMagnification       #10',
        '_rlnDetectorPixelSize   #11',
        '_rlnCtfFigureOfMerit    #12',
        '_rlnCtfMaxResolution    #13',
        ''
    ])
    rows = []
    for ad, mcd, cd in [(mg.acquisition_data, mg.motion_correction_data, mg.ctf_data) for mg in micrographs]:
        row = ' '.join([
            f'{mcd.image_link_path}',
            f'{cd.image_link_path}',
            f'{cd.defocus_u}',
            f'{cd.defocus_v}',
            f'astigmatism',
            f'{cd.astigmatism_angle}',
            f'{ad.voltage}',
            f'{ad.spherical_aberration}',
            f'{ad.amplitude_contrast}',
            f'{ad.nominal_magnification}',
            f'{mcd.pixel_size}',
            f'{cd.cross_correlation}',
            f'{cd.estimated_resolution}'
        ])
        rows.append(row)
    out_string += '\n'.join(rows)
    return out_string

# From https://stackoverflow.com/questions/8299386/modifying-a-symlink-in-python/55742015#55742015
def symlink(target, link_name, overwrite=False):
    '''
    Create a symbolic link named link_name pointing to target.
    If link_name exists then FileExistsError is raised, unless overwrite=True.
    When trying to overwrite a directory, IsADirectoryError is raised.
    '''

    if not overwrite:
        os.symlink(target, linkname)
        return

    # os.replace() may fail if files are on different filesystems
    link_dir = os.path.dirname(link_name)

    # Create link to target with temporary filename
    while True:
        temp_link_name = tempfile.mktemp(dir=link_dir)

        # os.* functions mimic as closely as possible system functions
        # The POSIX symlink() returns EEXIST if link_name already exists
        # https://pubs.opengroup.org/onlinepubs/9699919799/functions/symlink.html
        try:
            os.symlink(target, temp_link_name)
            break
        except FileExistsError:
            pass

    # Replace link_name with temp_link_name
    try:
        # Pre-empt os.replace on a directory with a nicer message
        if os.path.isdir(link_name):
            raise IsADirectoryError(f"Cannot symlink over existing directory: '{link_name}'")
        os.replace(temp_link_name, link_name)
    except:
        if os.path.islink(temp_link_name):
            os.remove(temp_link_name)
        raise