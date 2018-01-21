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
from collection_parser import IdogpickerParser, ParserProcess, MotionCor2Parser, GctfParser, StackParser, MontageParser, PickParser, NavigatorParser
from idogpicker_processor import IdogpickerProcessor
from random import randint
from time import sleep

config = {}
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
        image = imaging.load(filename)[0]
        image = imaging.filters.norm(image, 0.01, 0.01, 0, 255)
        image = imaging.filters.zoom(image, self.zoom)
        picks_path = pyfs.rext(filename) + self.suffix + '.preview.png'
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
    with open(args.config, 'r') as config_file:
        exec(config_file.read(), globals())
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

if __name__ == '__main__':
    start_processing()
