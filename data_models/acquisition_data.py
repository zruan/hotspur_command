from data_models import DataModel

class AcquisitionData(DataModel):

	def __init__(self, base_name):
		super().__init__(base_name)

		self.image_path = None
		self.file_format = None

		self.instrument = None
		self.voltage = None
		self.gain_reference_file = None

		self.total_dose = None
		self.exposure_time = None
		self.frame_count = None
		self.frame_dose = None
		self.pixel_size = None
		self.binning = None
