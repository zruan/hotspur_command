from data_models import DataModel

class AcquisitionData(DataModel):

    def __init__(self, base_name):
        super().__init__(base_name)

        self.image_path = None
        self.file_format = None

        self.instrument = None
        self.nominal_magnification = None
        self.camera = None
        self.gain_reference_file = None

        self.voltage = None
        self.spherical_aberration = None
        self.amplitude_contrast = None

        self.total_dose = None
        self.exposure_time = None
        self.frame_count = None
        self.frame_dose = None
        self.pixel_size = None
        self.binning = None
        self.dimensions = None

        self.stage_x = None
        self.stage_y = None
        self.stage_z = None
        self.stage_tilt = None
        self.image_shift_x = None
        self.image_shift_y = None
