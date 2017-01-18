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



class Parser:

    def __init__(self, database):
        self.database = database


class GctfParser(Parser):

    def __init__(self, database, config):
        Parser.__init__(self, database)
        self.config = config["GctfParser"] 

    def parse(self, num_files_max=-1):
        num_files = 0
        for key, value in self.database.items():
            if "Gctf" in value:
                continue
            ctf_files = glob.glob(string.Template(self.config["ctf_image_glob"]).substitute(base=key))
            if len(ctf_files) > 0:
                print("No Gctf parsed for %s . Processing ... " % (key),end="",flush=True)
                value["Gctf"] = {}
                value["Gctf"]["ctf_image_filename"] = ctf_files[-1]
                value["Gctf"]["ctf_preview_image_filename"] = string.Template(self.config["ctf_image_preview_glob"]).substitute(base=key)
                value["Gctf"]["ctf_star_filename"] = string.Template(self.config["ctf_star_glob"]).substitute(base=key)
                value["Gctf"]["ctf_epa_log_filename"] = string.Template(self.config["ctf_epa_log_glob"]).substitute(base=key)
                value["Gctf"]["ctf_log_filename"] = string.Template(self.config["ctf_log_glob"]).substitute(base=key)
                self.parse_EPA_log(value["Gctf"]["ctf_epa_log_filename"],value)
                self.parse_gctf_log(value["Gctf"]["ctf_log_filename"],value)
                print("Done!")
                num_files += 1

            if "num_files_max" in self.config and num_files_max > 0 and num_files >= self.config["num_files_max"]:
                break

    def parse_EPA_log(self, filename, value):
        data = np.genfromtxt(filename,skip_header=1,dtype=[float,float,float,float,float],usecols=(0,1,2,3,4))
        value["Gctf"]["EPA"] = {}
        value["Gctf"]["EPA"]["Resolution"] = list(data['f0'])
        value["Gctf"]["EPA"]["Sim. CTF"] = list(data['f1'])
        value["Gctf"]["EPA"]["Meas. CTF"] = list(data['f2'])
        value["Gctf"]["EPA"]["Meas. CTF - BG"] = list(data['f3'])

    def parse_gctf_log(self, filename, value):
        with open(filename) as f:
            lines = f.readlines()
        ctf_params = lines[-13].split()
        value["Gctf"]["Defocus U"] = ctf_params[0]
        value["Gctf"]["Defocus V"] = ctf_params[1]
        value["Gctf"]["Astig angle"] = ctf_params[2]
        value["Gctf"]["Phase shift"] = ctf_params[3]
        value["Gctf"]["CCC"] = ctf_params[4]
        value["Gctf"]["Estimated resolution"] = lines[-11].split()[-1]
        value["Gctf"]["Estimated b-factor"] = lines[-10].split()[-1]
        value["Gctf"]["Validation scores"] = [lines[a].split()[-1] for a in [-2,-3,-4,-5]]

class MotionCor2Parser(Parser):

    def __init__(self, database, config):
        Parser.__init__(self, database)
        self.config = config["MotionCor2Parser"] 

    def parse(self, num_files_max=-1):
        num_files = 0
        for key, value in self.database.items():
            if "MotionCor2" in value:
                continue
            sum_micrograph_files = glob.glob(string.Template(self.config["sum_micrograph_glob"]).substitute(base=key))
            if len(sum_micrograph_files) > 0:
                print("No MotionCor parsed for %s . Processing ... " % (key),end="",flush=True)
                value["MotionCor2"] = {}
                value["MotionCor2"]["sum_micrograph_filename"] = sum_micrograph_files[-1]
                value["MotionCor2"]["dw_micrograph_filename"] = string.Template(self.config["dw_micrograph_glob"]).substitute(base=key)
                value["MotionCor2"]["log_filename"] = string.Template(self.config["log_glob"]).substitute(base=key)
                self.parse_log(key,value["MotionCor2"]["log_filename"])
                value["Preview"] = {}
                value["Preview"]["filename"] =string.Template(self.config["preview_glob"]).substitute(base=key)
                print("Done!")
                num_files += 1

            if "num_files_max" in self.config and num_files_max > 0 and num_files >= self.config["num_files_max"]:
                break

    def parse_log(self, base, filename):
        with open(filename,"r") as fp:
            shifts=False
            self.database[base]["MotionCor2"]["x_shifts"] = []
            self.database[base]["MotionCor2"]["y_shifts"] = []
            for line in fp:
                if shifts:
                    if line.find(':') >= 0:
                        numbers = line.split(':')[1]
                        (x_shift, y_shift) = [float(x) for x in numbers.split()]
                        self.database[base]["MotionCor2"]["x_shifts"].append(x_shift)
                        self.database[base]["MotionCor2"]["y_shifts"].append(y_shift)
                    else:
                        shifts=False
                if line.find('Full-frame alignment shift') >= 0:
                    shifts=True


class StackParser(Parser):

    def __init__(self, database, config):
        Parser.__init__(self, database)
        self.config = config
        self.glob = config["glob"]

    def parse(self, num_files_max=-1):
        files = glob.glob(self.glob)
        num_files = 0
        for filename in files:
            base = pyfs.rext(filename)
            if base not in self.database:
                print("Found new stack %s under %s . Processing ... " % (base, filename), end="",flush=True)
                try:
                    self.analyze_file(base, filename)
                    print(" Done!")
                except:
                    print(" Unsuccesful!" , sys.exc_info()[0])
                num_files += 1

            if "num_files_max" in self.config and num_files_max > 0 and num_files >= self.config["num_files_max"]:
                break

    def analyze_file(self, base, filename):

        try:
            header = imaging.formats.FORMATS["mrc"].load_header(filename)
            try:
                acquisition_time = dateutil.parser.parse(header['labels'][0].decode().split()[-2] + " "+header['labels'][0].decode().split()[-1])
            except Exception as e:
                print("No date in header ... ",end="",flush=True)
                print(e)
                acquisition_time = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
            numframes = int(header['dims'][2])
            dimensions = (int(header['dims'][0]),int(header['dims'][1]))
            dose_per_frame = float(header['mean'])
            self.database[base] = { "moviestack" : { "filename" : filename,
                                                     "numframes" : numframes,
                                                     "acquisition_time" : acquisition_time.replace(tzinfo=tzlocal()).isoformat(),
                                                     "dimensions" : dimensions,
                                                     "dose_per_pix_frame": dose_per_frame }}
        except AttributeError as e:
            print(e)
        except:
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
        
        os.chdir(self.config["scratch_dir"])
        config = self.config["parser"]
        try:
            with open(config["Database"]) as database:
                database = json.load(database, object_pairs_hook=OrderedDict)
        except FileNotFoundError:
            database = OrderedDict()
        stackparser = StackParser(database, config["StackParser"])
        motioncor2parser = MotionCor2Parser(database, config)
        gctfparser = GctfParser(database, config)
        while True:

            stackparser.parse()

            motioncor2parser.parse()


            gctfparser.parse()
            
            with open(config["Database"], 'w') as outfile:
                    json.dump(database, outfile)
            time.sleep(2)
            


if __name__ == '__main__':
    from collection_processor import CommandProcessor, PreviewProcessor
    
    args = arguments()
    print(args)

    with open(args.config, 'r') as config_file:
        exec(config_file.read(), globals())
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


