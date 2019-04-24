import string
import os
import sys

from parsers import Parser
from data_models import AcquisitionDataModel

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
        mdoc_file_path = filename + '.mdoc'
        if os.path.isfile(mdoc_file_path):
            data_model = AcquisitionDataModel()
            data_model._id = AcquisitionDataModel.generate_id(base)
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
            data_model.save_to_couchdb(self.db)
