from data_models import DataModel


class MotionCorrectionData(DataModel):

	def __init__(self, base_name):
		super().__init__(base_name)

		self.aligned_image_file = None
		self.dose_weighted_image_file = None
		self.preview_file = None

		self.shift_list = None
		self.initial_shift = None
		self.total_shift = None

		self.pixel_size = None
		self.dimensions = None
