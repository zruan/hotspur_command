import os
from glob import glob

import couchdb

import hotspur_setup
from data_models import SessionData, AcquisitionData
from processors import motioncor2_processor_factory, gctf_processor_factory, ctffind_processor_factory
from processors import motioncor2_preview_processor_factory, gctf_preview_processor_factory, ctffind_preview_processor_factory


def _get_default_config():
    return {
        "user": None,
        "sample": None,
        "session": None,

        "frames_directory": None,
        "gainref" : None,
        "scratch_dir": None,
        "lock_dir": None,

        "voltage": 300,
        "pixel_size" : 1.72,
        "dose_rate" : None,
        "ac": 0.1,
        "binning": 0.5,
        "phaseplate" : False,
        "frame_count": None
    }

def _find_gain_reference(directory_path):
    ref_glob = "*Ref*.dm4"
    globn = os.path.join(directory_path, ref_glob)
    gain_refs = glob(globn)
    try:
        return gain_refs[0]
    except:
        print("Couldn't find a gain ref file in '{}' using glob '{}'", directory_path, ref_glob)

def _get_couchdb_database(user, grid, session):
    couch = couchdb.Server(hotspur_setup.couchdb_address)

    database_name = '_'.join([user, grid, session])
    database_name = database_name.lower()

    try:
        db = couch.create(database_name)
    except couchdb.http.PreconditionFailed:
        db = couch[database_name]

    return db

def _read_sample_mdoc(directory_path):
    search_glob = '*.mdoc'
    full_glob = os.path.join(directory_path, search_glob)
    results = glob(full_glob)

    if results.count == 0:
        print("Couldn't find any files matching '")
        print('Exiting...')
        exit()

    mdoc_file_path = results[0]
    if os.path.isfile(mdoc_file_path):
        data_model = AcquisitionData('sample')
        with open(mdoc_file_path, 'r') as mdoc:
            for line in mdoc.readlines():
                # key-value pairs are separated by ' = ' in mdoc files
                if not ' = ' in line:
                    continue
                key, value = [item.strip() for item in line.split(' = ')]
                # DEBUG print("Key: '{}'".format(key), "Value: '{}'".format(value))
                if key == 'Voltage':
                    data_model.voltage = int(value)
                elif key == 'ExposureDose':
                    data_model.total_dose = float(value)
                elif key == "ExposureTime":
                    data_model.exposure_time = float(value)
                elif key == 'PixelSpacing':
                    data_model.pixel_size = float(value)
                elif key == 'Binning':
                    data_model.binning = float(value)
                elif key == 'NumSubFrames':
                    data_model.frame_count = int(value)
                elif key == 'GainReference':
                    data_model.gain_reference_name = value
    return data_model

def generate_config(frames_directory):
    config = _get_default_config()

    frames_directory = os.path.abspath(frames_directory) + '/'
    session_directory = os.path.join(frames_directory, os.pardir)
    sample_directory = os.path.join(session_directory, os.pardir)
    user_directory = os.path.join(sample_directory, os.pardir)
 
    session_id = os.path.basename(os.path.normpath(session_directory))
    sample_id = os.path.basename(os.path.normpath(sample_directory))
    user_id = os.path.basename(os.path.normpath(user_directory))

    scratch_dir = "{}/{}/{}__{}/".format(hotspur_setup.base_path, user_id, sample_id, session_id)

    db = _get_couchdb_database(user_id, sample_id, session_id)
    try:
        session_data = SessionData.read_from_couchdb_by_name(db)
    except:
        session_data = SessionData()
        session_data.session = session_id
        session_data.grid = sample_id
        session_data.user = user_id
        session_data.frames_directory = frames_directory
        session_data.processing_directory = scratch_dir
        session_data.save_to_couchdb(db)

    tif_glob = "*.tif*"
    globn = os.path.join(frames_directory, tif_glob)
    tif_files = glob(globn)

    mrc_glob = "*.mrc"
    globn = os.path.join(frames_directory, mrc_glob)
    mrc_files = glob(globn)

    if len(tif_files) > len(mrc_files):
        filetype = 'tif'
    else:
        filetype = 'mrc'
    
    config['filetype'] = filetype

    config['user'] = user_id
    config['sample'] = sample_id
    config['session'] = session_id

    config['frames_directory'] = frames_directory
    # for backwards compatability
    config['collection_dir'] = frames_directory
    config['scratch_dir'] = scratch_dir
    config['lock_dir'] = os.path.join(scratch_dir, "lock") + '/' 

    config['gain_ref'] = _find_gain_reference(frames_directory)

    mdoc_data = _read_sample_mdoc(frames_directory)

    config['voltage'] = mdoc_data.voltage
    config['pixel_size'] = mdoc_data.pixel_size
    config['binning'] = mdoc_data.binning
    config['total_dose'] = mdoc_data.total_dose
    config['exposure_time'] = mdoc_data.exposure_time
    config['frame_count'] = mdoc_data.frame_count
    config['frame_dose'] = mdoc_data.total_dose / mdoc_data.exposure_time / mdoc_data.frame_count

    return config

def initialize_processes(config):
    processes = []

    processes.append(motioncor2_processor_factory.get_motioncor2_processor(config))
    # processes.append(gctf_processor_factory.get_gctf_processor(config))
    # processes.append(ctffind_processor_factory.get_ctffind_processor(config))

    # processes.append(motioncor2_preview_processor_factory.get_motioncor2_prev_processor(config))
    # processes.append(gctf_preview_processor_factory.get_gctf_prev_processor(config))
    # processes.append(ctffind_preview_processor_factory.get_gctf_prev_processor(config))

    return processes

def initialize(frames_directory):
    config = generate_config(frames_directory)
    processes = initialize_processes(config)
    return config, processes
