#!/eppec/storage/sw/hotspur_dev/venv/bin/python
from multiprocessing import Process
import sys
import glob
import os
from string import Template
import subprocess
import time
import argparse
import string
import getpass
import pyfs
import stat
import imaging
from collection_processor_base import CollectionProcessor
from collection_parser import IdogpickerParser, ParserProcess, MotionCor2Parser, GctfParser, StackParser, MontageParser, PickParser, NavigatorParser
from idogpicker_processor import IdogpickerProcessor
from random import randint
from time import sleep
import hashlib
import hotspur_setup

config = {
        # Directory that will be scanned for micrographs
        "collection_dir" : "/goliath/rawdata/BaconguisLab/posert/hotspur_default",
        # Glob that will be used to scan for new mrc files
        "glob" : "*/*.tif",
        # Scratch directo where data processing will be done. Should be an SSD
        "scratch_dir" : "/hotspur/scratch/posert/hotspur_default/scratch",
        # Archive dir. If configured files will be moved there fore permanent storage
        "archive_dir" : "/tmp/JE_test_archive/",
        # Directory that holds lock files for processing
        "lock_dir"    : "/hotspur/scratch/posert/hotspur_default/scratch/lock/",
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
                "ctf_star" : "${base}_mc_DW_gctf.star",
                "ctf_epa_log" : "${base}_mc_DW_EPA.log",
                "ctf_log" : "${base}_mc_DW_gctf.log"
                },
        #    "ctffind4" : {
        #         "type" : CtffindParser,
        #         "depends" : "ctffind",
        #         "ctf_image" : "${base}_mc_DW_ctffind.ctf",
        #         "ctf_image_preview" : "${base}_mc_DW_ctffind_ctf.preview.png",
        #         "ctf_epa_log" : "${base}_mc_DW_ctffind_avrot.txt",
        #         "ctf_log" : "${base}_mc_DW_ctffind.txt"
        #    },
           "moviestack" : {
               "type": StackParser,
               "depends" : "motioncor2",
               "moviestack" : "${collection_dir}${base}.tif"
               },
           "navigator" : {
               "type": NavigatorParser,
               "glob" : "${collection_dir}*.nav",
               "stackname_lambda" : lambda x, config : pyfs.rext(x[len(config["collection_dir"]):],full=True),
               "navigatorfile" : "${collection_dir}${base}.nav",
	       "run_once" : True
               },
           "idogpicker" : {
               "type": IdogpickerParser,
               "depends" : "idogpicker",
               "filename" : "${base}_mc_DW.idogpicker.json"
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

processes = []





class PreviewProcessor(CollectionProcessor):

    def __init__(self,
                 process_id,
                 config,
                 filename,
                 suffix="",
                 zoom=0.25,
                 **kwargs):
        CollectionProcessor.__init__(self, process_id, config, **kwargs)
        self.suffix = suffix
        self.zoom = zoom
        self.filename = filename

    def create_preview(self, filename):
        image_data = imaging.load(filename)
        for i, image in enumerate(image_data):
            if len(image_data) == 1:
                num = ""
            else:
                num = str(i)
            image = imaging.filters.norm(image, 0.01, 0.01, 0, 255)
            image = imaging.filters.zoom(image, self.zoom)
            picks_path = pyfs.rext(filename) + self.suffix + num + '.preview.png'
            imaging.save(image, picks_path)

    def run_loop(self, config, replace_dict):
        self.create_preview(
            string.Template(self.filename).substitute(replace_dict))


class CommandProcessor(CollectionProcessor):

    def __init__(self, process_id, process_command, config, **kwargs):
        CollectionProcessor.__init__(self, process_id, config, **kwargs)
        self.process_command = process_command

    def run_loop(self, config, replace_dict):
        command = Template(self.process_command).substitute(replace_dict)
        res = subprocess.run(command, shell=True)


def get_user_id_hash(user_id):
    m = hashlib.md5()
    m.update(user_id.encode('utf-8'))
    m.update(hotspur_setup.hash_salt.encode('utf-8'))
    digest = m.hexdigest()
    print("User ID hash is: {0}".format(digest))
    return digest


def prepare_directory_structure(config):
    if not os.path.exists(config["scratch_dir"]):
        os.makedirs(config["scratch_dir"])
    if not os.path.exists(config["lock_dir"]):
        os.makedirs(config["lock_dir"])

    # Create symlink to project's processing dir, to be consumed by hotspur web.
    user_path = os.path.abspath(os.path.join(config["scratch_dir"], os.pardir))
    user_id_hash = get_user_id_hash(config["user_id"])
    symlink_path = os.path.join(hotspur_setup.hashlinks_dir, user_id_hash)
    if not os.path.exists(symlink_path):
        os.symlink(user_path, symlink_path)


def arguments():
    parser = argparse.ArgumentParser(
        description='Runs data processing live for incoming data'
    )
    parser.add_argument(
        'config',
        help='Configuration file to use'
    )
    parser.add_argument(
        '--reset',
        help="Remove all '.done' files that track processing progress.",
        action='store_true'
    )
    return parser.parse_args()


def prepare_gain_reference(gain_ref, scratch_dir):
    # gain_ref =  os.path.normpath()
    _, ext = os.path.splitext(gain_ref)
    target_filename = "gainRef.mrc"
    target_path = os.path.join(scratch_dir, target_filename)

    if not os.path.exists(target_path):
        if ext == '.mrc':
            os.system("cp {} {}".format(gain_ref, target_path))
        elif ext == '.dm4':
            os.system("dm2mrc {} {}".format(gain_ref, target_path))
        else:
            raise ValueError('Gain reference is not ".dm4" or ".mrc" format.')

    print(target_path)
    return target_path


def reset_processing():
    print("Removing '.done' files...")
    for file in os.listdir(config['lock_dir']):
        if file.endswith('.done'):
            file_path = os.path.join(config['lock_dir'], file)
            os.remove(file_path)
    print("Successfully removed '.done' files.")


def start_processing():
    args = arguments()

    # execute the config file
    with open(args.config, 'r') as config_file:
        exec(config_file.read(), globals())
        # configure_project(), defined in config.py, updates the config dict
        # with user values and returns the correct list of processors and parsers.
        processes = configure_project(config)

    prepare_directory_structure(config)

    if args.reset:
        reset_processing()
        sys.exit()

    ref_path = prepare_gain_reference(
        config['gain_ref'], config['scratch_dir'])
    config['gainref'] = ref_path

    parse_process = ParserProcess(config)

    for process in processes:
        process.start()
    parse_process.start()
    try:
        for process in processes:
            process.join()
        parse_process.join()
    except KeyboardInterrupt:
        print("Waiting for processes to finish")
        for process in processes:
            process.join()
        parse_process.join()

if __name__ == '__main__':
    start_processing()
