#!/eppec/storage/sw/cky-tools/site/bin/python
from __future__ import print_function
import sys
import glob
import os
import datetime
import dateutil
import dateutil.parser
import pyfs
import imaging
import json
from collections import OrderedDict
import argparse
import numpy as np
import string
from dateutil.tz import tzlocal
from multiprocessing import Process
import time
import signal


class DelayedKeyboardInterrupt(object):
    def __enter__(self):
        self.signal_received = False
        self.old_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self.handler)

    def handler(self, sig, frame):
        self.signal_received = (sig, frame)

    def __exit__(self, type, value, traceback):
        signal.signal(signal.SIGINT, self.old_handler)
        if self.signal_received:
            self.old_handler(*self.signal_received)


class Parser:

    def __init__(self, parser_id, database, config, global_config):
        self.parser_id = parser_id
        self.database = database
        self.config = config
        self.global_config = global_config
        if "glob" in config:
            self.glob = config["glob"]
        elif "depends" in config:
            self.glob = (global_config["lock_dir"]
                         + pyfs.rext(global_config["glob"])
                         + "." + config["depends"] + ".done")
        else:
            raise ValueError(self.parserid
                             + ": Need to specify etiher watch_glob or dependency")

    def parse(self):
        num_files = 0
        files = glob.glob(self.glob)
        for filename in files:
            if "depends" in self.config:
                filename = filename[len(self.global_config["lock_dir"]):]
            if "stackname_lambda" in self.config:
                stackname = self.config["stackname_lambda"](filename)
            else:
                stackname = pyfs.rext(filename, full=True)
            if stackname in self.database and self.parser_id in self.database[stackname]:
                continue
            if stackname not in self.database:
                self.database[stackname] = {}
            print("%s: Parsing %s ..." % (self.parser_id, stackname))
            self.parse_process(stackname)
            num_files += 1
            print("Done!")
            if ("num_files_max" in self.config
                    and num_files >= self.config["num_files_max"]) or num_files > 10:
                break
        return num_files


class GctfParser(Parser):

    def parse_process(self, stackname):
        value = self.database[stackname]
        value[self.parser_id] = {}
        value[self.parser_id]["ctf_image_filename"] = string.Template(self.config["ctf_image"]).substitute(base=stackname)
        value[self.parser_id]["ctf_preview_image_filename"] = string.Template(self.config["ctf_image_preview"]).substitute(base=stackname)
        value[self.parser_id]["ctf_star_filename"] = string.Template(self.config["ctf_star"]).substitute(base=stackname)
        value[self.parser_id]["ctf_epa_log_filename"] = string.Template(self.config["ctf_epa_log"]).substitute(base=stackname)
        value[self.parser_id]["ctf_log_filename"] = string.Template(self.config["ctf_log"]).substitute(base=stackname)
        self.parse_EPA_log(value[self.parser_id]["ctf_epa_log_filename"], value[self.parser_id])
        self.parse_gctf_log(value[self.parser_id]["ctf_log_filename"], value[self.parser_id])

    def parse_EPA_log(self, filename, value):
        """Parses the EPA log of Gctf to provide radial average of CTF"""
        data = np.genfromtxt(filename,
                             skip_header=1,
                             dtype=[float, float, float, float, float],
                             usecols=(0, 1, 2, 3, 4))
        value["EPA"] = {}
        value["EPA"]["Resolution"] = list(data['f0'])
        value["EPA"]["Sim. CTF"] = list(data['f1'])
        value["EPA"]["Meas. CTF"] = list(data['f2'])
        value["EPA"]["Meas. CTF - BG"] = list(data['f3'])

    def parse_gctf_log(self, filename, value):
        with open(filename) as f:
            lines = f.readlines()
        for line in reversed(lines):
            if "Final Values" in line:
                ctf_params = line.split()
                value["Defocus U"] = ctf_params[0]
                value["Defocus V"] = ctf_params[1]
                value["Astig angle"] = ctf_params[2]
                value["Phase shift"] = ctf_params[3]
                value["CCC"] = ctf_params[4]
                break
            if "RES_LIMIT" in line:
                value["Estimated resolution"] = line.split()[-1]
            if "B_FACTOR" in line:
                value["Estimated b-factor"] = line.split()[-1]
        value["Validation scores"] = [lines[a].split()[-1] for a in [-2, -3, -4, -5]]


class MotionCor2Parser(Parser):

    def parse_process(self, stackname):
        value = self.database[stackname]
        value[self.parser_id] = {}
        value[self.parser_id]["sum_micrograph_filename"] = string.Template(self.config["sum_micrograph"]).substitute(base=stackname)
        value[self.parser_id]["dw_micrograph_filename"] = string.Template(self.config["dw_micrograph"]).substitute(base=stackname)
        value[self.parser_id]["log_filename"] = string.Template(self.config["log"]).substitute(base=stackname)
        value[self.parser_id]["preview_filename"] =string.Template(self.config["preview"]).substitute(base=stackname)
        self.parse_log(stackname,value["MotionCor2"]["log_filename"])

    def parse_log(self, base, filename):
        try:
            with open(filename,"r") as fp:
                shifts=False
                self.database[base][self.parser_id]["x_shifts"] = []
                self.database[base][self.parser_id]["y_shifts"] = []
                for line in fp:
                    if shifts:
                        if line.find(':') >= 0:
                            numbers = line.split(':')[1]
                            (x_shift, y_shift) = [float(x) for x in numbers.split()]
                            self.database[base][self.parser_id]["x_shifts"].append(x_shift)
                            self.database[base][self.parser_id]["y_shifts"].append(y_shift)
                        else:
                            shifts=False
                    if line.find('Full-frame alignment shift') >= 0:
                        shifts=True
        except IOError:
            print("No log found")


class StackParser(Parser):

    def parse_process(self, stackname):
        try:
            filename = string.Template(self.config["moviestack"]).substitute(base=stackname)
            self.analyze_file(stackname, filename)
            print(" Done!")
        except IOError:
            print(" Unsuccesful!" , sys.exc_info())


    def analyze_file(self, base, filename):

        try:
            if not os.path.isfile(filename):
                print(filename+".bz2")
                acquisition_time = datetime.datetime.fromtimestamp(os.path.getmtime(filename+".bz2"))
                self.database[base][self.parser_id] = { "filename" : filename,
                                                     "acquisition_time" : acquisition_time.replace(tzinfo=tzlocal()).isoformat() }
                return
            else:
                header = imaging.formats.FORMATS["mrc"].load_header(filename)
            try:
                acquisition_time = dateutil.parser.parse(header['labels'][0].decode().split()[-2] + " "+header['labels'][0].decode().split()[-1])
            except ValueError as e:
                print("No date in header ... ",end="",flush=True)
                print(e)
                acquisition_time = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
            numframes = int(header['dims'][2])
            dimensions = (int(header['dims'][0]),int(header['dims'][1]))
            dose_per_frame = float(header['mean'])
            self.database[base][self.parser_id] = { "filename" : filename,
                                                     "numframes" : numframes,
                                                     "acquisition_time" : acquisition_time.replace(tzinfo=tzlocal()).isoformat(),
                                                     "dimensions" : dimensions,
                                                     "dose_per_pix_frame": dose_per_frame }
        except AttributeError as e:
            print(e)
        except IOError:
            print("Error loading mrc!" , sys.exc_info()[0])
              
            raise

def arguments():

    def floatlist(string):
        return list(map(float, string.split(',')))

    parser = argparse.ArgumentParser(
        description='Parses information within a SerialEM data collection directory to a JSON file')
    parser.add_argument('--glob', help='glob pattern for MRC images')
    parser.add_argument('--json', help='glob pattern for MRC images')
    parser.add_argument('--config', default="config.py")
    parser.add_argument('--numfiles', default=-1, help='Number of images to process in this run', type=int)
    parser.add_argument('--skip_stack', default=False, action='store_true')
    
    return parser.parse_args()

class ParserProcess(Process):
    def __init__(self, config, work_dir=None):
        Process.__init__(self)
        self.config = config
        if work_dir is None:
            self.work_dir = config["scratch_dir"]
        else:
            self.work_dir = work_dir

    def run(self):
        seconds = 0
        if "work_dir" in self.config["parser"]:
            os.chdir(self.config["parser"]["work_dir"])
        else:
            os.chdir(self.config["scratch_dir"])
        config = self.config["parser"]
        try:
            with open(config["Database"]) as database:
                database = json.load(database, object_pairs_hook=OrderedDict)
        except FileNotFoundError:
            database = OrderedDict()
        parsers = []
        for (key,value) in config.items():
            if type(value) is dict:
                parsers.append(value["type"](key, database, value, self.config))

        while True:
            try:
                with DelayedKeyboardInterrupt():
                    parsed = 0
                    for parser in parsers:
                        parsed += parser.parse()
                    if parsed > 0:
                        with open(config["Database"], 'w') as outfile:
                            json.dump(database, outfile)
                        seconds = 0
                    else:
                        seconds += 2
                    if seconds > 3600:
                        print("Nothing parsed for 60 minutes. Exiting.")
                        break
                    time.sleep(2)
            except KeyboardInterrupt:
                print("Parser recieved Ctr-C")
                break
            


if __name__ == '__main__':
    from collection_processor import CommandProcessor, PreviewProcessor
    
    args = arguments()
    print(args)

    with open(args.config, 'r') as config_file:
        exec(config_file.read(), globals())
    if "work_dir" in config["parser"]:
        os.chdir(config["parser"]["work_dir"])
    else:
        os.chdir(config["scratch_dir"])

    config = config["parser"]

    if args.glob:
        config["StackParser"]["glob"] = args.glob
    if args.json:
        config["Database"] = args.json

    try:
        database = json.load(open(config["Database"]), object_pairs_hook=OrderedDict)
    except FileNotFoundError:
        database = OrderedDict()

    if not args.skip_stack:
        StackParser = StackParser(database, config["StackParser"])

        StackParser.parse()
    with open(config["Database"], 'w') as outfile:
            json.dump(database, outfile)

    MotionCor2Parser = MotionCor2Parser(database, config)

    MotionCor2Parser.parse()

    GctfParser = GctfParser(database, config)

    GctfParser.parse()
    
    with open(config["Database"], 'w') as outfile:
            json.dump(database, outfile)


