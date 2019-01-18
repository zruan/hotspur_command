#!/eppec/storage/sw/cky-tools/site/bin/python
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
from collection_parser import IdogpickerParser, ParserProcess, MotionCor2Parser, GctfParser, StackParser, MontageParser, PickParser, NavigatorParser, CtffindParser, Negstainparser
from idogpicker_processor import IdogpickerProcessor
from random import randint
from time import sleep

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
           "ctffind4" : {
                "type" : CtffindParser,
                "depends" : "ctffind",
                "ctf_image" : "${base}_mc_DW_ctffind.ctf",
                "ctf_image_preview" : "${base}_mc_DW_ctffind_ctf.preview.png",
                "ctf_epa_log" : "${base}_mc_DW_ctffind_avrot.txt",
                "ctf_log" : "${base}_mc_DW_ctffind.txt"
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


def arguments():
    def floatlist(string):
        return list(map(float, string.split(',')))

    parser = argparse.ArgumentParser(
        description='Runs data processing live for incoming data')

    parser.add_argument('--init', default=None,
                        help='Initiates configuration file. Should be adjusted before starting')
    parser.add_argument('--list', default=False, action='store_true',
                        help='List available configuration templates')
    parser.add_argument(
        '--config', help='Configuration file to use', default="config.py")

    return parser.parse_args()


def start_processing():
    args = arguments()
    print(args)
    if args.list:
        file_list = glob.glob(os.path.join(os.path.dirname(
            __file__), "collection_processor/config*.py"))
        for filename in file_list:
            print(os.path.basename(filename)[7:-3])
        sys.exit()

    if args.init is not None:
        try:
            with open(os.path.join(os.path.dirname(__file__), "collection_processor/config_" + args.init + ".py"), 'r') as config_file:
                template = string.Template(config_file.read())
        except IOError as e:
            print ("Config %s not found" % (args.init))
            sys.exit()
        config_processed = template.substitute(curr_dir=os.getcwd(),
                                               user=getpass.getuser(),
                                               curr_dir_base=os.path.basename(os.path.normpath(os.getcwd())))
        with open(args.config, 'w') as config_file:
            config_file.write(config_processed)
        sys.exit()

    # execute the config file
    with open(args.config, 'r') as config_file:
        exec(config_file.read(), globals())
        # configure_project(), defined in config.py, updates the config dict
        # with user values and returns the correct list of processors and parsers.
        processes = configure_project(config)
    if not os.path.exists(config["scratch_dir"]):
        os.makedirs(config["scratch_dir"])
    if not os.path.exists(config["lock_dir"]):
        os.makedirs(config["lock_dir"])

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
    except exception as e:
        print(e)

if __name__ == '__main__':
    start_processing()
