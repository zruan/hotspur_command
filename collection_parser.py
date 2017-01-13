#!/eppec/storage/sw/cky-tools/site/bin/python
from __future__ import print_function
import sys
import glob
import os
import datetime
import dateutil
import pyfs
import imaging
import json
from collections import OrderedDict
import argparse
import numpy as np
import string



config = { "MotionCor2Parser" : {
                "sum_micrograph_glob" : "${base}_mc.mrc",
                "dw_micrograph_glob" : "${base}_mc_DW.mrc",
                "log_glob" : "${base}_mc.log"
                },
           "PreviewParser" : {
                "image_glob" : "${base}_mc_prev.preview.png"
                },
           "GctfParser" : {
                "ctf_image_glob" : "${base}_mc_DW_ctf.mrc",
                "ctf_image_preview_glob" : "${base}_mc_DW_ctf_prev.preview.png",
                "ctf_star_glob" : "${base}_mwc_DW_gctf.star",
                "ctf_epa_log_glob" : "${base}_mc_DW_EPA.log",
                "ctf_log_glob" : "${base}_mc_DW_gctf.log"
                }
         }

class Parser:

    def __init__(self, database):
        self.database = database

class PreviewParser(Parser):

    def __init__(self, database, config):
        Parser.__init__(self, database)
        self.config = config["PreviewParser"] 


    def parse(self, num_files_max=-1):
        num_files = 0
        for key, value in self.database.items():
            if "Preview" in value:
                continue
            print("No preview image for %s . Processing ... " % (key),end="",flush=True)
            preview_files = glob.glob(string.Template(self.config["image_glob"]).substitute(base=key))
            if len(preview_files) > 0:
                value["Preview"] = {}
                value["Preview"]["filename"] = preview_files[-1]
                print("Done!")
            else:
                print("Not found!")

class GctfParser(Parser):

    def __init__(self, database, config):
        Parser.__init__(self, database)
        self.config = config["GctfParser"] 

    def parse(self, num_files_max=-1):
        num_files = 0
        for key, value in self.database.items():
            if "Gctf" in value:
                continue
            print("No Gctf parsed for %s . Processing ... " % (key),end="",flush=True)
            ctf_files = glob.glob(string.Template(self.config["ctf_image_glob"]).substitute(base=key))
            if len(ctf_files) > 0:
                value["Gctf"] = {}
                value["Gctf"]["ctf_image_filename"] = ctf_files[-1]
                value["Gctf"]["ctf_preview_image_filename"] = string.Template(self.config["ctf_image_preview_glob"]).substitute(base=key)
                value["Gctf"]["ctf_star_filename"] = string.Template(self.config["ctf_star_glob"]).substitute(base=key)
                value["Gctf"]["ctf_epa_log_filename"] = string.Template(self.config["ctf_epa_log_glob"]).substitute(base=key)
                value["Gctf"]["ctf_log_filename"] = string.Template(self.config["ctf_log_glob"]).substitute(base=key)
                self.parse_EPA_log(value["Gctf"]["ctf_epa_log_filename"],value)
                self.parse_gctf_log(value["Gctf"]["ctf_log_filename"],value)
                print("Done!")
            else:
                print("Not found!")

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
            print("No MotionCor parsed for %s . Processing ... " % (key),end="",flush=True)
            sum_micrograph_files = glob.glob(string.Template(self.config["sum_micrograph_glob"]).substitute(base=key))
            if len(sum_micrograph_files) > 0:
                value["MotionCor2"] = {}
                value["MotionCor2"]["sum_micrograph_filename"] = sum_micrograph_files[-1]
                dw_micrograph_files = glob.glob(string.Template(self.config["dw_micrograph_glob"]).substitute(base=key))
                if len(dw_micrograph_files) > 0:
                    value["MotionCor2"]["dw_micrograph_filename"] = dw_micrograph_files[-1]
                log_files = glob.glob(string.Template(self.config["log_glob"]).substitute(base=key))
                if len(log_files) > 0:
                    value["MotionCor2"]["log_filename"] = log_files[-1]
                    self.parse_log(key,value["MotionCor2"]["log_filename"])
                print("Done!")
            else:
                print("Not found!")

            num_files += 1
            if num_files_max > 0 and num_files >= num_files_max:
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

    def __init__(self, database, glob):
        Parser.__init__(self, database)
        self.glob = glob

    def parse(self, num_files_max=-1):
        files = glob.glob(self.glob)
        num_files = 0
        for filename in files:
            base = pyfs.rext(pyfs.bname(filename))
            if base not in self.database:
                print("Found new stack %s under %s . Processing ... " % (base, filename), end="",flush=True)
                try:
                    self.analyze_file(base, filename)
                    print(" Done!")
                except:
                    print(" Unsuccesful!" , sys.exc_info()[0])
                num_files += 1
            if num_files_max > 0 and num_files >= num_files_max:
                break

    def analyze_file(self, base, filename):

        try:
            header = imaging.formats.FORMATS["mrc"].load_header(filename)
            try:
                acquisition_time = dateutil.parser.parse(header[18][0].split()[-2].decode() + " "+header[18][0].split()[-1].decode())
            except:
                print("No date in header ... ",end="",flush=True)
                acquisition_time = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
            data = imaging.load(filename)
            numframes = data.shape[0]
            dimensions = (data.shape[1],data.shape[2])
            if data.shape[2] < 2000:
                print("Packed ...",end="",flush=True)
                e_sum = float(np.bitwise_and(data, 0x0f).sum()) + float(np.bitwise_and(data >> 4,0x0f).sum())
                dose_per_frame = e_sum / data.shape[0] / data.shape[1] / data.shape[2] / 2
            else:
                e_sum = float(data.sum())
                dose_per_frame = e_sum / data.shape[0] / data.shape[1] / data.shape[2]
            self.database[base] = { "moviestack" : { "filename" : filename,
                                                     "numframes" : numframes,
                                                     "acquisition_time" : acquisition_time.isoformat(),
                                                     "dimensions" : dimensions,
                                                     "e_sum": e_sum,
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
    
    parser.add_argument('--json',  help='path to JSON file')
    parser.add_argument('--glob', help='glob pattern for MRC images')
    parser.add_argument('--numfiles', default=-1, help='Number of images to process in this run', type=int)
    parser.add_argument('--skip_stack', default=False, action='store_true')
    
    return parser.parse_args()



if __name__ == '__main__':
    
    args = arguments()
    print(args)

    try:
        database = json.load(open(args.json), object_pairs_hook=OrderedDict)
    except FileNotFoundError:
        database = OrderedDict()

    if not args.skip_stack:
        StackParser = StackParser(database, args.glob)

        StackParser.parse(num_files_max=args.numfiles)
    with open(args.json, 'w') as outfile:
            json.dump(database, outfile)

    MotionCor2Parser = MotionCor2Parser(database, config)

    MotionCor2Parser.parse(num_files_max=args.numfiles)

    PreviewParser = PreviewParser(database, config)

    PreviewParser.parse(num_files_max=args.numfiles)
    
    GctfParser = GctfParser(database, config)

    GctfParser.parse(num_files_max=args.numfiles)
    
    with open(args.json, 'w') as outfile:
            json.dump(database, outfile)


