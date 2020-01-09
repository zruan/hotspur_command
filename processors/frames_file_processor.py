import os
import time
from pathlib import Path
import tifffile
import imaging

from utils.logging import get_logger_for_module
from data_models import AcquisitionData, UserData


logger = get_logger_for_module(__name__)

class FramesFileProcessor():

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

        self.suffixes= ['.tif', '.mrc']
        # Time (sec) to wait before acting on a file. Prevents reading a partial file.
        self.min_lifetime = 120
        self.batch_size = 20

        self.tracked = []
        self.queued = []

        self.sync_with_db()

    def sync_with_db(self):
        present_data = AcquisitionData.fetch_all(self.session.db)
        self.tracked = [d.image_path for d in present_data]
        logger.debug(f"Fetched aquisition data models for session {self.session.name}")


    def run(self):
        images = self.find_images()
        images = self.filter_for_untracked_images(images)
        self.tracked.extend([i.image_path for i in images])
        images = self.filter_for_present_metadata(images)
        stacks = self.filter_for_framestacks(images)
        self.queued.extend(stacks)
        stacks = self.get_valid_stacks_from_queue()
        stacks = self.filter_for_most_recent_stacks(stacks)

        for stack in stacks:
            try:
                self.parse_stack(stack)
                stack.push(self.session.db)
                user_data = UserData(stack.base_name)
                user_data.push(self.session.db)
                self.update_session(stack)
                self.queued.remove(stack)
            except Exception as e:
                logger.exception(e)
                continue


    def find_images(self):
        found_images = []
        for suffix in self.suffixes:
            image_paths = Path(self.session.directory).glob(f'**/*{suffix}')
            images = [self.model_image(p) for p in image_paths]
            found_images.extend(images)
        return found_images


    def model_image(self, image_path):
        data_model = AcquisitionData(image_path.stem)
        data_model.image_path = str(image_path)
        data_model.file_format = image_path.suffix
        data_model.data_file_path = f'{image_path}.mdoc'
        data_model.data_file_format = '.mdoc'
        data_model.time = image_path.stat().st_mtime
        return data_model


    def filter_for_untracked_images(self, images):
        return [i for i in images if i.image_path not in self.tracked]


    def filter_for_present_metadata(self, images):
        return [i for i in images if self.metadata_present(i)]


    def metadata_present(self, image):
        return Path(image.data_file_path).exists()


    def filter_for_framestacks(self, images):
        return [i for i in images if self.is_framestack(i)]


    def is_framestack(self, image):
        num_frame_sets = 0
        with open(image.data_file_path, 'r') as mdoc:
            for line in mdoc.readlines():
                if line.startswith("[FrameSet"):
                    num_frame_sets += 1
        return num_frame_sets == 1


    def get_valid_stacks_from_queue(self):
        return [i for i in self.queued if self.validate_stack(i)]


    def validate_stack(self, image):
        age = self.get_image_age(image.image_path)
        return age >= self.min_lifetime


    def get_image_age(self, image_path):
        last_activity = Path(image_path).stat().st_mtime
        current_time = time.time()
        age_in_seconds = current_time - last_activity
        return age_in_seconds


    def filter_for_most_recent_stacks(self, stacks):
        stacks.sort(key=lambda i: i.time, reverse=True)
        return stacks[:self.batch_size]


    def parse_stack(self, stack):
        stack.spherical_aberration = 2.7
        stack.amplitude_contrast = 0.1
        self.update_model_from_mdoc(stack)
        try:
            self.update_dose_from_image(stack)
        except Exception as e:
            logger.exception(e)


    def update_model_from_mdoc(self, data_model):
        with open(data_model.data_file_path, 'r') as mdoc:
            for line in mdoc.readlines():
                # key-value pairs are separated by ' = ' in mdoc files
                if not ' = ' in line:
                    continue

                try:
                    key, value = [item.strip() for item in line.split(' = ')]
                except:
                    continue

                if key == 'Voltage':
                    data_model.voltage = int(value)
                elif key == 'ExposureDose':
                    data_model.total_dose = float(value)
                elif key == "ExposureTime":
                    data_model.exposure_time = float(value)
                elif key == 'PixelSpacing':
                    data_model.pixel_size = float(value)
                elif key == 'Binning':
                    data_model.binning = float(value)
                elif key == 'NumSubFrames':
                    data_model.frame_count = int(value)
                elif key == 'GainReference':
                    gain_ref_path = Path(data_model.data_file_path).parent / value
                    data_model.gain_reference_file = str(gain_ref_path)
                elif key == 'Magnification':
                    data_model.nominal_magnification = value
                elif key == 'StagePosition':
                    data_model.stage_x =  float(value.split(" ")[0])
                    data_model.stage_y =  float(value.split(" ")[1])
                elif key == 'StageZ':
                    data_model.stage_z = float(value)
                elif key == 'TiltAngle':
                    data_model.stage_tilt = float(value)
                elif key == 'ImageShift':
                    data_model.image_shift_x =  float(value.split(" ")[0])
                    data_model.image_shift_y =  float(value.split(" ")[1])
                elif key == 'RotationAngle':
                    data_model.rotation_angle = float(value)

        return data_model

    def update_dose_from_image(self, data_model):
        if data_model.file_format == '.tif':
            frame_dose_per_pixel, dimensions = self.get_dose_from_tif(data_model.image_path) 
        elif data_model.file_format == '.mrc':
            frame_dose_per_pixel, dimensions = self.get_dose_from_mrc(data_model.image_path)

        data_model.frame_dose = frame_dose_per_pixel / (data_model.pixel_size ** 2)
        data_model.total_dose = data_model.frame_dose * data_model.frame_count
        data_model.dimensions = dimensions 
        return data_model
    


    def get_dose_from_tif(self, tif_path):
        with tifffile.TiffFile(tif_path) as imfile:
            return (imfile.pages[0].asarray().mean(), imfile.pages[0].asarray().shape[::-1])


    def get_dose_from_mrc(self, mrc_path):
        imfile = imaging.load(mrc_path)
        return (imfile.mean(), imfile.shape[-2::-1])


    def update_session(self, data_model):
        if self.session.time is None or data_model.time < self.session.time:
            self.session.time = data_model.time
            self.session.push(self.session.db)

        if self.session.end_time is None or data_model.time > self.session.end_time:
            self.session.end_time = data_model.time
            self.session.push(self.session.db)
