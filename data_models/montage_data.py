from data_models import DataModel

class MontageData(DataModel):

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
        self.pixel_size = None
        self.binning = None
        self.dimensions = None

        self.stage_tilt = None
        self.rotation_angle = None
        self.number_tiles = None
