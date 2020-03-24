import os
import sys
import time
import imaging
from threading import Lock, Thread
import subprocess
import math
from itertools import accumulate
import glob
from pathlib import Path


from data_models import AcquisitionData, MotionCorrectionData, DataModelList
from utils.resources import ResourceManager
from utils.config import get_config
from utils.logging import get_logger_for_module

LOG = get_logger_for_module(__name__)


class Motioncor2Processor():

    required_gpus = 1
    processors_by_session = {}
    target_binning = 1

    tracking_interval = 20

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
        self.failed = []
        self.time_since_last_tracking = None
        self.sync_with_db()

    def sync_with_db(self):
        self.model_list_mc = DataModelList(MotionCorrectionData, self.session.db)
        self.model_list_fra = DataModelList(AcquisitionData, self.session.db)
        #current_models = MotionCorrectionData.fetch_all(self.session.db)
        base_names = [model.base_name for model in self.model_list_mc.models]
        self.tracked = base_names.copy()
        self.finished = base_names.copy()


    def update_tracked_data(self):
        self.model_list_fra.update()
        #current_models = AcquisitionData.fetch_all(self.session.db)
        for model in  self.model_list_fra.models:
            if model.base_name not in self.tracked:
                self.tracked.append(model.base_name)
                self.queued.append(model)
        self.queued.sort(key=lambda model: model.time)

    def run(self):
        if self.time_since_last_tracking is None or time.time() - self.time_since_last_tracking >= Motioncor2Processor.tracking_interval:
            LOG.debug("Starting tracking")
            self.update_tracked_data()
            LOG.debug("Finished tracking")
            self.time_since_last_tracking = time.time()

        if len(self.queued) == 0:
            return

        gpu_id_list = ResourceManager.request_gpus(Motioncor2Processor.required_gpus)
        if gpu_id_list is not None:
            try:
                acquisition_data_model = self.queued.pop()
                process_thread = Thread(
                    target=self.process_data,
                    args=(acquisition_data_model, gpu_id_list)
                )
                process_thread.start()
            except:
                ResourceManager.release_gpus(gpu_id_list)

    def process_data(self, acquisition_data_model, gpu_id_list):
        try:
            gain_file = self.prepare_gain_reference(
                self.session.processing_directory, acquisition_data_model.gain_reference_file, acquisition_data_model
            )
        except Exception as e:
            LOG.exception(f'Error preparing gain reference for {acquisition_data_model.base_name} in {self.session.long_name}: {e}')
            self.failed.append(acquisition_data_model.base_name)
            ResourceManager.release_gpus(gpu_id_list)
            return
            
        output_file_base = '{}/{}'.format(self.session.processing_directory,
                                          acquisition_data_model.base_name)
        output_file = '{}_mc.mrc'.format(output_file_base)
        output_file_dose_weighted = '{}_mc_DW.mrc'.format(output_file_base)
        output_log_file = '{}_mc.log'.format(output_file_base)

        bin_amount = int(Motioncor2Processor.target_binning / acquisition_data_model.binning)
        input_flag = '-InTiff' if acquisition_data_model.file_format == '.tif' else '-InMrc'

        dose_per_pixel = acquisition_data_model.frame_dose * (acquisition_data_model.pixel_size ** 2)
        
        # Try to automatically choose grouping. Should have 0.4e/pix/frame, but make sure not too much grouping.
        group_amount = math.ceil(0.4 / dose_per_pixel)
        if group_amount > (acquisition_data_model.frame_count / 3):
            group_amount = math.floor(acquisition_data_model.frame_count/3)
        if group_amount > 7:
            group_amount = 7

        command_list = [
            f'{get_config().motioncor2_full_path}',
            f'{input_flag} {acquisition_data_model.image_path}',
            f'-OutMrc {output_file}',
            f'-Group {group_amount}',
            f'-Kv {acquisition_data_model.voltage}',
            f'-gain {gain_file}',
            f'-PixSize {acquisition_data_model.pixel_size}',
            f'-FmDose {acquisition_data_model.frame_dose}',
            f'-FtBin {bin_amount}' if bin_amount != 1 else '',
            '-Iter 10',
            '-Tol 0.5',
            '-Gpu {}'.format(','.join([str(gpu_id) for gpu_id in gpu_id_list])),
            f'> {output_log_file}'
        ]
        # print(' '.join(command_list))
        subprocess.call(' '.join(command_list), shell=True)

        data_model = MotionCorrectionData(acquisition_data_model.base_name)
        data_model.time = time.time()
        data_model.non_weighted_image_file = output_file
        data_model.log_file = output_log_file
        data_model.binning = Motioncor2Processor.target_binning
        data_model.grouped_by = group_amount
        data_model.command_list = command_list

        if os.path.exists(output_file_dose_weighted):
            data_model.dose_weighted_image_file = output_file_dose_weighted
            data_model.corrected_image_file = output_file_dose_weighted
        else:
            data_model.corrected_image_file = output_file
        data_model.preview_file = self.create_preview(
            data_model.corrected_image_file)

        try:
            data_model = self.populate_shifts_from_log(data_model, output_log_file)
        except Exception as e:
            LOG.exception(f'Error reading shifts of {data_model.base_name} in {self.session.long_name}: {e}')
            self.failed.append(data_model.base_name)
            ResourceManager.release_gpus(gpu_id_list)
            return

        try:
            data_model = self.populate_image_metadata_from_mrc(data_model, output_file)
        except Exception as e:
            LOG.exception(f'Error populating image metadata of {data_model.base_name} in {self.session.long_name}: {e}')
            self.failed.append(data_model.base_name)
            ResourceManager.release_gpus(gpu_id_list)
            return

        try:
            data_model.push(self.session.db)
        except Exception as e:
            LOG.exception(f'Error pushing results to db {data_model.base_name} in {self.session.long_name}: {e}')
            self.failed.append(data_model.base_name)
            ResourceManager.release_gpus(gpu_id_list)
            return


        self.finished.append(data_model.base_name)

        ResourceManager.release_gpus(gpu_id_list)

    def create_preview(self, file):
        try:
            image = imaging.load(file)[0]
            image = imaging.filters.norm(image, 0.01, 0.01, 0, 255)
            image = imaging.filters.zoom(image, 0.25)
            preview_file = '{}.preview.png'.format(file)
            imaging.save(image, preview_file)
            return preview_file
        except Exception as e:
            print(e)
            return None

    def populate_shifts_from_log(self, data_model, output_log_file):
        try:
            # MotionCor2 outputs movements relative to the first frame (aka displacements),
            # not movements relative to the previous frame (aka shifts)
            with open(output_log_file, "r") as fp:
                displacements = []
                shifts = []
                reading_shifts = False
                for line in fp:
                    if reading_shifts:
                        if not 'shift' in line:
                            reading_shifts = False
                            continue

                        columns = line.split()
                        displacement = (float(columns[-2]), float(columns[-1]))
                        displacements.append(displacement)

                        if len(displacements) < 2:
                            continue

                        prev_displacement = displacements[-2]
                        shift = (
                            displacement[0] - prev_displacement[0],
                            displacement[1] - prev_displacement[1]
                        )
                        shifts.append(shift)

                    elif 'Full-frame alignment shift' in line:
                        reading_shifts=True

            distances=[math.sqrt(x**2 + y**2) for x, y in shifts]
            accumulated_distances=list(accumulate(distances))

            data_model.shift_list = shifts
            data_model.displacement_list = displacements
            data_model.distance_list = distances
            data_model.accumulated_distance_list = accumulated_distances

            data_model.initial_distance = distances[0]
            data_model.total_displacement = displacements[-1]
            data_model.early_accumulated_distance = accumulated_distances[2]
            data_model.late_accumulated_distance = (
                accumulated_distances[-1] - accumulated_distances[2]
            )
            data_model.total_accumulated_distance = accumulated_distances[-1]

            return data_model
        except Exception as e:
            print(e)
            raise e

    def populate_image_metadata_from_mrc(self, data_model, mrc_file):
        try:
            header=imaging.formats.FORMATS["mrc"].load_header(mrc_file)
            dimensions=(int(header['dims'][0]), int(header['dims'][1]))
            pixel_size=float(header['lengths'][0]/header['dims'][0])

            data_model.dimensions = dimensions
            data_model.pixel_size = pixel_size
            return data_model
        except AttributeError as e:
            print(e)
            raise e
        except IOError as e:
            print("Error loading mrc!", sys.exc_info()[0])
            raise e
        except Exception as e:
            print(e)
            raise e

    def prepare_gain_reference(self, processing_directory, gain_file, acquisition_data_model):
        if gain_file is None or not os.path.exists(gain_file):
            collection_directory = Path(acquisition_data_model.data_file_path).parent
            potential_gain_files = glob.glob(os.path.join(collection_directory, "*.dm4"))
            potential_gain_files += glob.glob(os.path.join(collection_directory, "*[gG]ain*.mrc"))
            if len(potential_gain_files) < 1:
                raise ValueError('No valid gain mentioned in mdoc and mo potential gain files found')
            gain_file = potential_gain_files[0]
            LOG.info(f'No valid gain in mdoc, but potential gain files: {potential_gain_files}')

        basename = os.path.splitext(os.path.basename(gain_file))[0]
        target_filename=basename+".mrc"
        ext=os.path.splitext(gain_file)[1]
        target_path=os.path.join(processing_directory, target_filename)

        try:
            if not os.path.exists(target_path):
                if ext == '.mrc':
                    os.system("cp {} {}".format(gain_file, target_path))
                elif ext == '.dm4':
                    command_list = [
                        f'{get_config().imod_dm2mrc_full_path}',
                        f'{gain_file} {target_path}',
                    ]
                    subprocess.call(' '.join(command_list), shell=True)
                else:
                    raise ValueError('Gain reference is not ".dm4" or ".mrc" format.')
            return target_path
        except Exception as e:
            LOG.error(e)
            raise e
