import os
import time
from glob import glob
from threading import Thread
import subprocess
import imaging
import numpy as np

from data_models import AcquisitionData, MotionCorrectionData, CtfData 
from utils.resources import ResourceManager
from utils.config import get_config


class CtffindProcessor():

    required_cpus = 1
    processors_by_session = {}

    @classmethod
    def for_session(cls, session):
        try:
            return cls.processors_by_session[session]
        except:
            processor = cls(session)
            cls.processors_by_session[session] = processor
            return processor


    def __init__(self, session):
        self.session = session

        self.tracked = []
        self.queued = []
        self.finished = []

        self.sync_with_db()

    def sync_with_db(self):
        ctf_data_models = CtfData.fetch_all(self.session.db)
        base_names = [model.base_name for model in ctf_data_models]
        self.tracked = base_names.copy()
        self.finished = base_names.copy()

    def update_tracked_data(self):
        motion_data_model = MotionCorrectionData.fetch_all(self.session.db)
        for model in motion_data_model:
            if model.base_name not in self.tracked:
                self.tracked.append(model.base_name)
                self.queued.append(model)
        self.queued.sort(key=lambda model: model.time)

    def run(self):
        self.update_tracked_data()

        if len(self.queued) == 0:
            return

        if ResourceManager.request_cpus(CtffindProcessor.required_cpus):
            try:
                motion_correction_data = self.queued.pop()
                acquisition_data = AcquisitionData(motion_correction_data.base_name)
                acquisition_data.fetch(self.session.db)
                process_thread = Thread(
                    target=self.process_data,
                    args=(acquisition_data, motion_correction_data)
                )
                process_thread.start()
            except:
                ResourceManager.release_cpus(CtffindProcessor.required_cpus)

    def process_data(self, acquisition_data, motion_correction_data):
        if motion_correction_data.dose_weighted_image_file is not None:
            aligned_image_file = motion_correction_data.dose_weighted_image_file
        else:
            aligned_image_file = motion_correction_data.aligned_image_file
        output_file_base = os.path.join(self.session.processing_directory, acquisition_data.base_name)
        output_file = '{}_ctffind.ctf'.format(output_file_base)

        # Ctffind requires a HEREDOC. Yikes.
        command_list = [
            f'{get_config().ctffind_full_path} << EOF',
            aligned_image_file,
            output_file,
            '{}'.format(motion_correction_data.pixel_size), # pixelsize
            # '{}'.format(acquisition_data.voltage), # acceleration voltage
            '300',
            '2.70', # Cs
            '0.1', # amplitude contrast
            '512', # size of amplitude spectrum to compute
            '20', # min resolution
            '4', # max resolution
            '5000', # min defocus
            '50000', # max defoxus
            '500', # defocus search step
            'no', # is astig known
            'yes', # slower, more exhaustive search
            'yes', # use a restraint on astig
            '200.0', # expected (tolerated) astig
            'no', # find additional phase shift
            'no', # set expert options
            'EOF'
        ]

        subprocess.call('\n'.join(command_list), shell=True)

        data_model = CtfData(acquisition_data.base_name)
        data_model.time = time.time()
        data_model.ctf_image_file = output_file
        data_model.ctf_image_preview_file = self.create_preview(data_model.ctf_image_file)
        data_model.ctf_log_file = '{}_ctffind.txt'.format(output_file_base)
        data_model.ctf_epa_log_file = '{}_ctffind_avrot.txt'.format(output_file_base)

        try:
            data_model = self.update_model_from_EPA_log(data_model)
        except Exception as e:
            print("Failed to update ctf data from EPA log {}".format(data_model.ctf_epa_log_file))
            print(e)
            pass
        try:
            data_model = self.update_model_from_ctffind_log(data_model)
        except Exception as e:
            print("Failed to update ctf data from ctffind log {}".format(data_model.ctf_log_file))
            print(e)
            pass

        data_model.push(self.session.db)

        self.finished.append(data_model.base_name)

        ResourceManager.release_cpus(self.required_cpus)

    def create_preview(self, file):
        image = imaging.load(file)[0]
        image = imaging.filters.norm(image, 0.01, 0.01, 0, 255)
        # image = imaging.filters.zoom(image, 0.25)
        preview_file = '{}.preview.png'.format(file)
        imaging.save(image, preview_file)
        return preview_file

    def update_model_from_EPA_log(self, data_model):
        # ctffind4 log output filename: diagnostic_output_avrot.txt
        # columns:
        # 0 = spatial frequency (1/Angstroms)
        # 1 = 1D rotational average of spectrum (assuming no astigmatism)
        # 2 = 1D rotational average of spectrum
        # 3 = CTF fit
        # 4 = cross-correlation between spectrum and CTF fit
        # 5 = 2sigma of expected cross correlation of noise
        data = np.genfromtxt(
            data_model.ctf_epa_log_file,
            skip_header=5
        )
        # the first entry in spatial frequency is 0
        data[0] = np.reciprocal(data[0], where = data[0]!=0)
        data[0][0] = None

        data_model.spatial_frequency_axis = list(np.nan_to_num(data[0]))
        data_model.measured_ctf_curve = list(np.nan_to_num(data[2]))
        data_model.theoretical_ctf_curve = list(np.nan_to_num(data[3]))
        # value["EPA"]["Ctffind_CC"] = list(np.nan_to_num(data[4]))
        # value["EPA"]["Ctffind_CCnoise"] = list(np.nan_to_num(data[5]))
        return data_model

    def update_model_from_ctffind_log(self, data_model):
        # ctffind output is diagnostic_output.txt
        # the last line has the non-input data in it, space-delimited
        # values:
        # 0: micrograph number; 1: defocus 1 (A); 2: defocus 2 (A); 3: astig azimuth;
        # 4: additional phase shift (radians); 5: cross correlation;
        # 6: spacing (in A) up to which CTF fit
        with open(data_model.ctf_log_file) as f:
            lines = f.readlines()
        ctf_params = lines[5].split(' ')

        data_model.defocus_u = float(ctf_params[1])
        data_model.defocus_v = float(ctf_params[2])
        data_model.astigmatism = data_model.defocus_u - data_model.defocus_v
        data_model.astigmatism_angle = float(ctf_params[3])
        data_model.defocus = (data_model.defocus_u + data_model.defocus_v) / 2
        data_model.phase_shift = float(ctf_params[4])
        data_model.cross_correlation = float(ctf_params[5])
        data_model.estimated_resolution = float(ctf_params[6].rstrip())
        data_model.estimated_b_factor = 0
        return data_model