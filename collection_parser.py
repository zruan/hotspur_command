#!/eppec/storage/sw/cky-tools/site/bin/python
from __future__ import print_function
import sys
import glob
import os
import datetime
import dateutil
import re
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
import traceback
# import pouchdb
import math


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
    def __init__(self, parser_id, database, config, global_config,db):
        self.parser_id = parser_id
        self.database = database
        self.config = config
        self.global_config = global_config
        self.db = db
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
                filename = filename[len(self.global_config["lock_dir"]):-len(".done")]
            if "stackname_lambda" in self.config:
                stackname = self.config["stackname_lambda"](filename,self.global_config)
            else:
                stackname = pyfs.rext(filename, full=False)
            if  ("run_once" not in self.config or self.config["run_once"]) and stackname in self.database and self.parser_id in self.database[
                    stackname]:
                continue
            if stackname not in self.database:
                self.database[stackname] = {}
            print("%s: Parsing %s ..." % (self.parser_id, stackname))
            try:
                self.parse_process(stackname)
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except:
                with open("parse_error.log", 'a') as fp:
                    traceback.print_exc(file=fp)
            num_files += 1
            print("Done!")
            if ("num_files_max" in self.config and num_files >=
                    self.config["num_files_max"]) or num_files > 500:
                break
        return num_files

class IdogpickerParser(Parser):
    def parse_process(self, stackname):
        value = self.database[stackname]
        value[self.parser_id] = {}
        value[self.parser_id]["idogpicker_filename"] = string.Template(
            self.config["filename"]).substitute(base=stackname)
        doc = {}
        doc['_id'] = stackname+"_particles_hotspurdefault"
        doc['micrograph'] = stackname
        doc['type'] = "particles"
        doc['program'] = "idogpicker"

        doc['idogpicker_file'] = string.Template(
            self.config["filename"]).substitute(base=stackname)
        self.db.save(doc)

class GctfParser(Parser):
    def parse_process(self, stackname):
        value = self.database[stackname]
        value[self.parser_id] = {}
        value[self.parser_id]["ctf_image_filename"] = string.Template(
            self.config["ctf_image"]).substitute(base=stackname,collection_dir=self.global_config["collection_dir"])
        value[self.parser_id]["ctf_preview_image_filename"] = string.Template(
            self.config["ctf_image_preview"]).substitute(base=stackname,collection_dir=self.global_config["collection_dir"])
        value[self.parser_id]["ctf_star_filename"] = string.Template(
            self.config["ctf_star"]).substitute(base=stackname,collection_dir=self.global_config["collection_dir"])
        value[self.parser_id]["ctf_epa_log_filename"] = string.Template(
            self.config["ctf_epa_log"]).substitute(base=stackname,collection_dir=self.global_config["collection_dir"])
        value[self.parser_id]["ctf_log_filename"] = string.Template(
            self.config["ctf_log"]).substitute(base=stackname,collection_dir=self.global_config["collection_dir"])
        self.parse_EPA_log(value[self.parser_id]["ctf_epa_log_filename"],
                           value[self.parser_id])
        self.parse_gctf_log(value[self.parser_id]["ctf_log_filename"],
                            value[self.parser_id])
        doc = {}
        doc['_id'] = stackname+"_ctf_hotspurdefault"
        doc['micrograph'] = stackname
        doc['type'] = "ctf"
        doc['program'] = "Gctf 1.06"

        doc['astigmatism_angle'] = value[self.parser_id]['Astig angle']
        doc['defocus_u'] = value[self.parser_id]['Defocus U']
        doc['defocus_v'] = value[self.parser_id]['Defocus V']
        #doc['ctf_measured'] = value[self.parser_id]['EPA']['Meas. CTF']
        #doc['ctf_measured_nobg'] = value[self.parser_id]['EPA']['Meas. CTF - BG']
        #doc['ctf_resolution_a'] = value[self.parser_id]['EPA']['Resolution']
        #doc['ctf_theory'] = value[self.parser_id]['EPA']['Sim. CTF']
        doc['estimated_b_factor'] = value[self.parser_id]['Estimated b-factor']
        doc['estimated_resolution'] = value[self.parser_id]['Estimated resolution']
        doc['cross_correlation'] = value[self.parser_id]['Phase shift']
        doc['gctf_validation_scores'] = value[self.parser_id]['Validation scores']
        doc['gctf_file_epa_log']  = value[self.parser_id]['ctf_epa_log_filename']
        doc['file_ctf_image'] = value[self.parser_id]['ctf_image_filename']
        doc['file_ctf_image_preview'] = value[self.parser_id]['ctf_preview_image_filename']
        doc['file_ctf_star'] = value[self.parser_id]['ctf_star_filename']
        doc['file_ctf_log'] = value[self.parser_id]['ctf_log_filename']
        doc['file_ctf_curve'] = stackname + "_ctfcurve.json"
        with open(doc['file_ctf_curve'], 'w') as outfile:
            json.dump({
                'ctf_measured': value[self.parser_id]["EPA"]["Meas. CTF"],
                'ctf_measured_nobg': value[self.parser_id]["EPA"]["Meas. CTF - BG"],
                'ctf_resolution_a': value[self.parser_id]["EPA"]["Resolution"],
                'ctf_theory': value[self.parser_id]["EPA"]["Sim. CTF"]
            }, outfile, allow_nan=False)

        self.db.save(doc)


    def parse_EPA_log(self, filename, value):
        """Parses the EPA log of Gctf to provide radial average of CTF"""
        data = np.genfromtxt(
            filename,
            skip_header=1,
            dtype=[float, float, float, float, float],
            usecols=(0, 1, 2, 3, 4))
        value["EPA"] = {}
        value["EPA"]["Resolution"] = list(data['f0'])
        value["EPA"]["Sim. CTF"] = list(np.nan_to_num(data['f1']))
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

class CtffindParser(Parser):
    def parse_process(self, stackname):
        value = self.database[stackname]
        value[self.parser_id] = {}
        value[self.parser_id]["ctf_image_filename"] = string.Template(
            self.config["ctf_image"]).substitute(base = stackname, collection_dir = self.global_config["collection_dir"])
        value[self.parser_id]["ctf_preview_image_filename"] = string.Template(
            self.config["ctf_image_preview"]).substitute(base = stackname, collection_dir = self.global_config["collection_dir"])
        value[self.parser_id]["ctf_epa_log_filename"] = string.Template(
            self.config["ctf_epa_log"]).substitute(base = stackname, collection_dir = self.global_config["collection_dir"])
        value[self.parser_id]["ctf_log_filename"] = string.Template(
            self.config["ctf_log"]).substitute(base = stackname, collection_dir = self.global_config["collection_dir"])

        self.parse_EPA_log(value[self.parser_id]["ctf_epa_log_filename"],
                           value[self.parser_id])
        self.parse_ctffind_log(value[self.parser_id]["ctf_log_filename"],
                            value[self.parser_id])
        doc = {}
        doc['_id'] = stackname+"_ctf_ctffind"
        doc['micrograph'] = stackname
        doc['type'] = "ctf"
        doc['program'] = "Ctffind 4"

        doc['astigmatism_angle'] = value[self.parser_id]['Astig angle']
        doc['defocus_u'] = value[self.parser_id]['Defocus U']
        doc['defocus_v'] = value[self.parser_id]['Defocus V']
        #doc['ctf_measured'] = value[self.parser_id]['EPA']['Meas. CTF']
        #doc['ctf_measured_nobg'] = value[self.parser_id]['EPA']['Meas. CTF - BG']
        #doc['ctf_resolution_a'] = value[self.parser_id]['EPA']['Resolution']
        #doc['ctf_theory'] = value[self.parser_id]['EPA']['Sim. CTF']
        doc['estimated_b_factor'] = value[self.parser_id]['Estimated b-factor']
        doc['estimated_resolution'] = value[self.parser_id]['Estimated resolution']
        doc['cross_correlation'] = value[self.parser_id]["CCC"]
        doc['gctf_file_epa_log']  = value[self.parser_id]['ctf_epa_log_filename']
        doc['file_ctf_image'] = value[self.parser_id]['ctf_image_filename']
        doc['file_ctf_image_preview'] = value[self.parser_id]['ctf_preview_image_filename']
        doc['file_ctf_log'] = value[self.parser_id]['ctf_log_filename']
        doc['file_ctf_curve'] = stackname + "_ctfcurve_ctffind.json"
        with open(doc['file_ctf_curve'], 'w') as outfile:
            json.dump({
                'ctf_measured': value[self.parser_id]["EPA"]["Meas. CTF"],
                'ctf_measured_nobg': value[self.parser_id]["EPA"]["Meas. CTF - BG"],
                'ctf_resolution_a': value[self.parser_id]["EPA"]["Resolution"],
                'ctf_theory': value[self.parser_id]["EPA"]["Sim. CTF"]
            }, outfile, allow_nan=False)

        self.db.save(doc)

    def parse_EPA_log(self, filename, value):
        # ctffind4 log output filename: diagnostic_output_avrot.txt
        # columns:
        # 0 = spatial frequency (1/Angstroms)
        # 1 = 1D rotational average of spectrum (assuming no astigmatism)
        # 2 = 1D rotational average of spectrum
        # 3 = CTF fit
        # 4 = cross-correlation between spectrum and CTF fit
        # 5 = 2sigma of expected cross correlation of noise
        data = np.genfromtxt(
            filename,
            skip_header=5
        )
        # the first entry in spatial frequency is 0
        data[0] = np.reciprocal(data[0], where = data[0]!=0)
        data[0][0] = None
        value["EPA"] = {}
        value["EPA"]["Resolution"] = list(np.nan_to_num(data[0]))
        value["EPA"]["Sim. CTF"] = list(np.nan_to_num(data[3]))
        value["EPA"]["Meas. CTF"] = list(np.nan_to_num(data[2]))
        value["EPA"]["Meas. CTF - BG"] = list(np.nan_to_num(data[5]))

    def parse_ctffind_log(self, filename, value):
        # ctffind output is diagnostic_output.txt
        # the last line has the non-input data in it, space-delimited
        # values:
        # 0: micrograph number; 1: defocus 1 (A); 2: defocus 2 (A); 3: astig azimuth;
        # 4: additional phase shift (radians); 5: cross correlation;
        # 6: spacing (in A) up to which CTF fit
        with open(filename) as f:
            lines = f.readlines()
        ctf_params = lines[5].split(' ')
        value["Defocus U"] = (float(ctf_params[1]))
        value["Defocus V"] = (float(ctf_params[2]))
        value["Astig angle"] = ctf_params[3]
        value["Phase shift"] = ctf_params[4]
        value["CCC"] = ctf_params[5]
        value["Estimated resolution"] = ctf_params[6]
        value["Estimated b-factor"] = 0

class Negstainparser(Parser):
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

        doc = {}
        doc['_id'] = stackname+"_motioncorrection_datajsonimport"
        doc['micrograph'] = stackname
        doc['type'] = "motioncorrection"
        doc['program'] = "Its just negativestain,come on"

        doc['file_dw'] = value[self.parser_id]['dw_micrograph_filename']
        doc['file_sum'] = value[self.parser_id]['sum_micrograph_filename']
        doc['file_log'] = value[self.parser_id]['log_filename']
        doc['file_preview'] = value[self.parser_id]['preview_filename']
        #doc['frame_shifts'] = [value[self.parser_id]['x_shifts'],value[self.parser_id]['y_shifts']]
        self.db.save(doc)

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

        doc = {}
        doc['_id'] = stackname+"_motioncorrection_datajsonimport"
        doc['micrograph'] = stackname
        doc['type'] = "motioncorrection"
        doc['program'] = "motioncor2 1.10"

        doc['dimensions'] = value[self.parser_id]['dimensions']
        doc['file_dw'] = value[self.parser_id]['dw_micrograph_filename']
        doc['file_sum'] = value[self.parser_id]['sum_micrograph_filename']
        doc['file_log'] = value[self.parser_id]['log_filename']
        doc['pixel_size'] = value[self.parser_id]['pixel_size']
        doc['file_preview'] = value[self.parser_id]['preview_filename']
        #doc['frame_shifts'] = [value[self.parser_id]['x_shifts'],value[self.parser_id]['y_shifts']]
        doc['initial_shift'] = math.sqrt(value[self.parser_id]['x_shifts'][1]**2 + value[self.parser_id]['y_shifts'][1]**2)
        total = 0
        for i,a in enumerate(value[self.parser_id]['x_shifts']):
            total += math.sqrt(a**2 + value[self.parser_id]['y_shifts'][i]**2)
        doc['total_shift'] = total
        doc['file_shifts'] = stackname + "_motioncor_shifts.json"
        with open(doc['file_shifts'], 'w') as outfile:
            json.dump([value[self.parser_id]['x_shifts'],value[self.parser_id]['y_shifts']],outfile)




        self.db.save(doc)

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
        preview_filename = base+"_preview.png"
        if not os.path.isfile(self.global_config["scratch_dir"]+preview_filename):
            self.analyze_mmm_file(base,filename,preview_filename, acquisition_time)
            return
        self.database[base][self.parser_id] = {
                "filename": filename,
                "preview_filename": base+"_preview.png",
                "acquisition_time":
                acquisition_time.replace(tzinfo=tzlocal()).isoformat(),
            }

    def analyze_mmm_file(self, base, filename, preview_filename, acquisition_time):
        i = 0
        while os.path.isfile(self.global_config["scratch_dir"] + "%s.%03d.png" % (preview_filename, i)):
            mmm_filename = ("%s.%03d.png" % (preview_filename, i))
            self.database[base+"%03d" % (i)] = {}
            self.database[base+"%03d" % (i)][self.parser_id] = {
                "filename": filename,
                "preview_filename": mmm_filename,
                "acquisition_time":
                acquisition_time.replace(tzinfo=tzlocal()).isoformat(),
            }
            self.database[base][self.parser_id] = {}
            i += 1

class NavigatorParser(Parser):
    def parse_process(self, stackname):
        try:
            filename = string.Template(self.config["navigatorfile"]).substitute(
                base=stackname,collection_dir=self.global_config["collection_dir"])
            self.analyze_file(stackname, filename)
        except IOError:
            print("Unsuccesful!", sys.exec_info())


    def analyze_file(self, base, filename):
        try:
            with open(filename, "r") as fp:
                self.database[base][self.parser_id] = {}
                self.database[base][self.parser_id]["items"] = []
                item = False
                for line in fp:
                    new_item_match = re.match(r"\[(.+)\]",line)
                    if not new_item_match is None:
                        item = { "Title" : new_item_match.group(1)}
                        self.database[base][self.parser_id]["items"].append(item)
                        continue
                    if item and len(line.split('=')) > 1:
                        item[line.split('=')[0].strip()] = line.split('=')[1].strip()
        except IOError:
            print("Can't open navigator")
        return



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
        if os.path.isfile(filename):
            star_data = pystar2.load(filename)['']
            fields = list(star_data)[0]
            if "picks" in self.database[base]:
                self.database[base]["picks"][self.parser_id] = []
            else:
                self.database[base]["picks"] = {}
                self.database[base]["picks"][self.parser_id] = []
            self.database[base][self.parser_id] = []
            index_x = fields.index('rlnCoordinateX')
            index_y = fields.index('rlnCoordinateY')
            index_psi = fields.index('rlnAnglePsi')
            index_class = fields.index('rlnClassNumber')
            index_FOM = fields.index('rlnAutopickFigureOfMerit')
            for pick in list(star_data.values())[0]:
                self.database[base]["picks"][self.parser_id].append(
                        { "x" : pick[index_x],
                          "y" : pick[index_y],
                          "psi" : pick[index_psi],
                          "cl" : pick[index_class],
                          "fom" : pick[index_FOM] } )
        else:
            if "picks" in self.database[base]:
                self.database[base]["picks"][self.parser_id] = []
            else:
                self.database[base]["picks"] = {}
                self.database[base]["picks"][self.parser_id] = []
            self.database[base][self.parser_id] = []





class StackParser(Parser):
    def parse_process(self, stackname):
        try:
            filename = string.Template(self.config["moviestack"]).substitute(
                base=stackname,collection_dir=self.global_config["collection_dir"])
            self.analyze_file(stackname, filename)
            print(" Done!")
        except IOError:
            self.database[stackname][self.parser_id] = {}
            print(" Unsuccesful!", sys.exc_info())
            raise

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
            numframes = 1
            dimensions =[1,1]
            dose_per_frame = 1
            try:
                header = imaging.formats.FORMATS["mrc"].load_header(filename)
                acquisition_time = dateutil.parser.parse(header['labels'][
                    0].decode().split()[-2] + " " + header['labels'][0].decode(
                    ).split()[-1])
                numframes = int(header['dims'][2])
                dimensions = (int(header['dims'][0]), int(header['dims'][1]))
                dose_per_frame = float(header['mean'])
            except (ValueError, IndexError) as e:
                print("No date in header ... ", end="", flush=True)
                try:
                    acquisition_time = datetime.datetime.strptime("_".join(pyfs.rext(filename.split('/')[-1]).split('_')[-3:-1]),"%b%d_%H.%M.%S")
                except ValueError:
                    print("Filename has no date")
                    print("_".join(pyfs.rext(filename.split('/')[-1]).split('_')[-3:-1]))
                    acquisition_time = datetime.datetime.fromtimestamp(
                      os.path.getmtime(filename))
            self.database[base][self.parser_id] = {
                "filename": filename,
                "numframes": numframes,
                "acquisition_time":
                acquisition_time.replace(tzinfo=tzlocal()).isoformat(),
                "dimensions": dimensions,
                "dose_per_pix_frame": dose_per_frame
            }
            doc = {}
            doc['_id'] = base+"_movie"
            doc['micrograph'] = base
            doc['type'] = "movie"

            doc['acquisition_time'] = self.database[base][self.parser_id]['acquisition_time']
            doc['dimensions'] = self.database[base][self.parser_id]['dimensions']
            doc['number_frames'] = self.database[base][self.parser_id]['numframes']
            doc['pixel_size'] = 0
            doc['dose_pixel_frame'] = self.database[base][self.parser_id]['dose_per_pix_frame']
            doc['file'] = self.database[base][self.parser_id]['filename']
            self.db.save(doc)
        except AttributeError as e:
            print(e)
            raise
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
    parser.add_argument('--refresh')
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

        couch = couchdb.Server('http://elferich:particles@localhost:5984/')

        user = os.path.split(self.config["scratch_dir"])[-2].split(os.sep)[-2].lower()
        dataset = os.path.split(self.config["scratch_dir"])[-2].split(os.sep)[-1].lower()
        try:
            db = couch.create(user+"_"+dataset)
        except couchdb.http.PreconditionFailed:
            db = couch[user+"_"+dataset]

        parsers = []
        for (key, value) in config.items():
            if type(value) is dict:
                parsers.append(value["type"](key, database, value,
                                             self.config,db))

        while True:
            try:
                with DelayedKeyboardInterrupt():
                    parsed = 0
                    for parser in parsers:
                        parsed += parser.parse()
                    if parsed > 0:

                        with open(config["Database"], 'w') as outfile:
                            json.dump(database, outfile, allow_nan=False)
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
    if args.refresh:
        if "work_dir" in config["parser"]:
            os.chdir(config["parser"]["work_dir"])
        else:
            os.chdir(config["scratch_dir"])
        with open(config["parser"]["Database"]) as database:
            database = json.load(database, object_pairs_hook=OrderedDict)
        for key in database.keys():
            if args.refresh in database[key]:
                del database[key][args.refresh]
        with open(config["parser"]["Database"], 'w') as outfile:
            json.dump(database, outfile)
        with gzip.open(config["parser"]["Database"]+".gz", 'wt') as outfile:
            json.dump(database, outfile)

    parse_process = ParserProcess(config)
    parse_process.start()
    try:
        parse_process.join()
    except KeyboardInterrupt:
        print("Waiting for processes to finish")
        parse_process.join()
