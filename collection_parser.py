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
import gzip
import pystar2

class FloatEncoder(json.JSONEncoder):
    def __init__(self, nan_str="null", **kwargs):
        super(FloatEncoder, self).__init__(**kwargs)
        self.nan_str = nan_str
        self.encoding = 'utf-8'

    def iterencode(self, o, _one_shot=False):
        """Encode the given object and yield each string
        representation as available.

        For example::

            for chunk in JSONEncoder().iterencode(bigobject):
                mysocket.write(chunk)
        """
        if self.check_circular:
            markers = {}
        else:
            markers = None
        if self.ensure_ascii:
            _encoder = json.encoder.encode_basestring_ascii
        else:
            _encoder = json.encoder.encode_basestring
        if self.encoding != 'utf-8':
            def _encoder(o, _orig_encoder=_encoder, _encoding=self.encoding):
                if isinstance(o, str):
                    o = o.decode(_encoding)
                return _orig_encoder(o)

        def floatstr(o, allow_nan=self.allow_nan, _repr=json.encoder.FLOAT_REPR,
                _inf=json.encoder.INFINITY, _neginf=-json.encoder.INFINITY,
                nan_str=self.nan_str):
            # Check for specials.  Note that this type of test is processor
            # and/or platform-specific, so do tests which don't depend on the
            # internals.

            if o != o:
                text = nan_str
            elif o == _inf:
                text = 'Infinity'
            elif o == _neginf:
                text = '-Infinity'
            else:
                return _repr(o)

            if not allow_nan:
                raise ValueError(
                    "Out of range float values are not JSON compliant: " +
                    repr(o))

            return text

        _iterencode = json.encoder._make_iterencode(
                markers, self.default, _encoder, self.indent, floatstr,
                self.key_separator, self.item_separator, self.sort_keys,
                self.skipkeys, _one_shot)
        return _iterencode(o, 0)

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
            self.glob = string.Template(config["glob"]).substitute(global_config)
        elif "depends" in config:
            self.glob = (
                global_config["lock_dir"] + pyfs.rext(global_config["glob"]) +
                "." + config["depends"] + ".done")
        else:
            raise ValueError(
                self.parserid +
                ": Need to specify either watch_glob or dependency")

    def parse(self):
        num_files = 0
        files = glob.glob(self.glob)
        for filename in files:
            if "depends" in self.config:
                filename = filename[len(self.global_config["lock_dir"]):]
            if "stackname_lambda" in self.config:
                stackname = self.config["stackname_lambda"](filename,self.global_config)
            else:
                stackname = pyfs.rext(filename, full=True)
            if stackname in self.database and self.parser_id in self.database[
                    stackname]:
                continue
            if stackname not in self.database:
                self.database[stackname] = {}
            print("%s: Parsing %s ..." % (self.parser_id, stackname))
            self.parse_process(stackname)
            num_files += 1
            print("Done!")
            if ("num_files_max" in self.config and num_files >=
                    self.config["num_files_max"]) or num_files > 10:
                break
        return num_files


class GctfParser(Parser):
    def parse_process(self, stackname):
        value = self.database[stackname]
        value[self.parser_id] = {}
        value[self.parser_id]["ctf_image_filename"] = string.Template(
            self.config["ctf_image"]).substitute(base=stackname)
        value[self.parser_id]["ctf_preview_image_filename"] = string.Template(
            self.config["ctf_image_preview"]).substitute(base=stackname)
        value[self.parser_id]["ctf_star_filename"] = string.Template(
            self.config["ctf_star"]).substitute(base=stackname)
        value[self.parser_id]["ctf_epa_log_filename"] = string.Template(
            self.config["ctf_epa_log"]).substitute(base=stackname)
        value[self.parser_id]["ctf_log_filename"] = string.Template(
            self.config["ctf_log"]).substitute(base=stackname)
        self.parse_EPA_log(value[self.parser_id]["ctf_epa_log_filename"],
                           value[self.parser_id])
        self.parse_gctf_log(value[self.parser_id]["ctf_log_filename"],
                            value[self.parser_id])

    def parse_EPA_log(self, filename, value):
        """Parses the EPA log of Gctf to provide radial average of CTF"""
        data = np.genfromtxt(
            filename,
            skip_header=1,
            dtype=[float, float, float, float, float],
            usecols=(0, 1, 2, 3, 4))
        value["EPA"] = {}
        value["EPA"]["Resolution"] = list(data['f0'])
        value["EPA"]["Sim. CTF"] = list(data['f1'])
        value["EPA"]["Meas. CTF"] = list(np.nan_to_num(data['f2']))
        value["EPA"]["Meas. CTF - BG"] = list(np.nan_to_num(data['f3']))

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
        value["Validation scores"] = [
            lines[a].split()[-1] for a in [-2, -3, -4, -5]
        ]


class MotionCor2Parser(Parser):
    def parse_process(self, stackname):
        value = self.database[stackname]
        value[self.parser_id] = {}
        value[self.parser_id]["sum_micrograph_filename"] = string.Template(
            self.config["sum_micrograph"]).substitute(base=stackname)
        value[self.parser_id]["dw_micrograph_filename"] = string.Template(
            self.config["dw_micrograph"]).substitute(base=stackname)
        value[self.parser_id]["log_filename"] = string.Template(self.config[
            "log"]).substitute(base=stackname)
        value[self.parser_id]["preview_filename"] = string.Template(
            self.config["preview"]).substitute(base=stackname)
        self.parse_log(stackname, value[self.parser_id]["log_filename"])
        self.parse_mrc(stackname, value[self.parser_id]["dw_micrograph_filename"])

    def parse_log(self, base, filename):
        try:
            with open(filename, "r") as fp:
                shifts = False
                self.database[base][self.parser_id]["x_shifts"] = []
                self.database[base][self.parser_id]["y_shifts"] = []
                for line in fp:
                    if shifts:
                        if line.find(':') >= 0:
                            numbers = line.split(':')[1]
                            (x_shift,
                             y_shift) = [float(x) for x in numbers.split()]
                            self.database[base][self.parser_id][
                                "x_shifts"].append(x_shift)
                            self.database[base][self.parser_id][
                                "y_shifts"].append(y_shift)
                        else:
                            shifts = False
                    if line.find('Full-frame alignment shift') >= 0:
                        shifts = True
        except IOError:
            print("No log found")
    
    def parse_mrc(self, base, filename):
        
        try:
            header = imaging.formats.FORMATS["mrc"].load_header(filename)
            dimensions = (int(header['dims'][0]), int(header['dims'][1]))
            pixel_size = float(header['lengths'][0]/header['dims'][0])
            self.database[base][self.parser_id]["dimensions"] = dimensions
            self.database[base][self.parser_id]["pixel_size"] = pixel_size
        except AttributeError as e:
            print(e)
        except IOError:
            print("Error loading mrc!", sys.exc_info()[0])

            raise

class MontageParser(Parser):
    def parse_process(self, stackname):
        try: 
            filename = string.Template(self.config["montage"]).substitute(
                base=stackname,collection_dir=self.global_config["collection_dir"])
            self.analyze_file(stackname, filename)
        except IOError:
            print("Unsuccesful!", sys.exec_info())


    def analyze_file(self, base, filename):
        header = imaging.formats.FORMATS["mrc"].load_header(filename)
        try:
            acquisition_time = dateutil.parser.parse(header['labels'][
                0].decode().split()[-2] + " " + header['labels'][0].decode(
                ).split()[-1])
        except ValueError as e:
            print("No date in header ... ", end="", flush=True)
            print(e)
            acquisition_time = datetime.datetime.fromtimestamp(
                os.path.getmtime(filename))
        self.database[base][self.parser_id] = {
                "filename": filename,
                "preview_filename": base+"_preview.png",
                "acquisition_time":
                acquisition_time.replace(tzinfo=tzlocal()).isoformat(),
            }


class PickParser(Parser):
    def parse_process(self, stackname):
        try:
            filename = string.Template(self.config["starfile"]).substitute(
                base=stackname)
            self.analyze_file(stackname, filename)
            print(" Done!")
        except IOError:
            print(" Unsuccesful!", sys.exc_info())

    def analyze_file(self, base, filename):
        star_data = pystar2.load(filename)['']
        fields = list(star_data)[0]
        self.database[base][self.parser_id] = []
        index_x = fields.index('rlnCoordinateX')
        index_y = fields.index('rlnCoordinateY')
        index_psi = fields.index('rlnAnglePsi')
        index_class = fields.index('rlnClassNumber')
        index_FOM = fields.index('rlnAutopickFigureOfMerit')
        for pick in list(star_data.values())[0]:
            self.database[base][self.parser_id].append(
                    { "x" : pick[index_x],
                      "y" : pick[index_y],
                      "psi" : pick[index_psi],
                      "cl" : pick[index_class],
                      "fom" : pick[index_FOM] } )

        



class StackParser(Parser):
    def parse_process(self, stackname):
        try:
            filename = string.Template(self.config["moviestack"]).substitute(
                base=stackname,collection_dir=self.global_config["collection_dir"])
            self.analyze_file(stackname, filename)
            print(" Done!")
        except IOError:
            print(" Unsuccesful!", sys.exc_info())

    def analyze_file(self, base, filename):

        try:
            if not os.path.isfile(filename):
                print(filename + ".bz2")
                acquisition_time = datetime.datetime.fromtimestamp(
                    os.path.getmtime(filename + ".bz2"))
                self.database[base][self.parser_id] = {
                    "filename": filename,
                    "acquisition_time":
                    acquisition_time.replace(tzinfo=tzlocal()).isoformat()
                }
                return
            header = imaging.formats.FORMATS["mrc"].load_header(filename)
            try:
                acquisition_time = dateutil.parser.parse(header['labels'][
                    0].decode().split()[-2] + " " + header['labels'][0].decode(
                    ).split()[-1])
            except ValueError as e:
                print("No date in header ... ", end="", flush=True)
                print(e)
                acquisition_time = datetime.datetime.fromtimestamp(
                    os.path.getmtime(filename))
            numframes = int(header['dims'][2])
            dimensions = (int(header['dims'][0]), int(header['dims'][1]))
            dose_per_frame = float(header['mean'])
            self.database[base][self.parser_id] = {
                "filename": filename,
                "numframes": numframes,
                "acquisition_time":
                acquisition_time.replace(tzinfo=tzlocal()).isoformat(),
                "dimensions": dimensions,
                "dose_per_pix_frame": dose_per_frame
            }
        except AttributeError as e:
            print(e)
        except IOError:
            print("Error loading mrc!", sys.exc_info()[0])

            raise


def arguments():
    def floatlist(string):
        return list(map(float, string.split(',')))

    parser = argparse.ArgumentParser(
        description='Parses information within a SerialEM data collection directory to a JSON file'
    )
    parser.add_argument('--glob', help='glob pattern for MRC images')
    parser.add_argument('--json', help='glob pattern for MRC images')
    parser.add_argument('--config', default="config.py")
    parser.add_argument(
        '--numfiles',
        default=-1,
        help='Number of images to process in this run',
        type=int)
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
        for (key, value) in config.items():
            if type(value) is dict:
                parsers.append(value["type"](key, database, value,
                                             self.config))

        while True:
            try:
                with DelayedKeyboardInterrupt():
                    parsed = 0
                    for parser in parsers:
                        parsed += parser.parse()
                    if parsed > 0:
                        
                        with open(config["Database"], 'w') as outfile:
                            json.dump(database, outfile)
                        with gzip.open(config["Database"]+".gz", 'wt') as outfile:
                            json.dump(database, outfile)
                        seconds = 0
                    else:
                        seconds += 2
                    if seconds > 36000:
                        print("Nothing parsed for 600 minutes. Exiting.")
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
    



    if args.glob:
        config["parser"]["StackParser"]["glob"] = args.glob
    if args.json:
        config["parser"]["Database"] = args.json

    parse_process = ParserProcess(config)
    parse_process.start()
    try:
        parse_process.join()
    except KeyboardInterrupt:
        print("Waiting for processes to finish")
        parse_process.join()
