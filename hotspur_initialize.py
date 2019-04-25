import os
from glob import glob

import hotspur_setup
from data_models import AcquisitionDataModel


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

def _read_sample_mdoc(directory_path):
    search_glob = '*.mdoc'
    full_glob = os.path.join(directory_path, search_glob)
    results = glob(full_glob)

    if results.count == 0:
        print("Couldn't find any files matching '")

    mdoc_file_path = results[0]
    if os.path.isfile(mdoc_file_path):
        data_model = AcquisitionDataModel()
        with open(mdoc_file_path, 'r') as mdoc:
            for line in mdoc.readlines():
                # key-value pairs are separated by ' = ' in mdoc files
                if not ' = ' in line:
                    continue
                key, value = [item.strip() for item in line.split(' = ')]
                # DEBUG print("Key: '{}'".format(key), "Value: '{}'".format(value))
                if key == 'Voltage':
                    data_model.voltage = value
                elif key == 'ExposureDose':
                    data_model.dose_rate = value
                elif key == 'PixelSpacing':
                    data_model.pixel_size = value
                elif key == 'Binning':
                    data_model.binning = value
                elif key == 'FrameDosesAndNumber':
                    data_model.frame_count = value.split()[-1]
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

    config['user'] = user_id
    config['sample'] = sample_id
    config['session'] = session_id

    config['frames_directory'] = frames_directory
    config['scratch_dir'] = scratch_dir
    config['lock_dir'] = os.path.join(scratch_dir, "lock") + '/' 

    config['gain_ref'] = _find_gain_reference(frames_directory)

    mdoc_data = _read_sample_mdoc(frames_directory)

    config['voltage'] = mdoc_data.voltage
    config['pixel_size'] = mdoc_data.pixel_size
    config['binning'] = mdoc_data.binning
    config['total_dose'] = mdoc_data.dose_rate
    config['frame_count'] = mdoc_data.frame_count

    return config
