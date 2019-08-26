from data_models import DataModel


class MotionCorrectionData(DataModel):

	def __init__(self, base_name):
		super().__init__(base_name)

		self.corrected_image_file = None
		self.non_weighted_image_file = None
		self.dose_weighted_image_file = None
		self.log_file = None
		self.preview_file = None

		self.shift_list = None
		self.displacement_list = None
		self.distance_list = None
		self.accumulated_distance_list = None

		self.initial_distance = None
		self.total_displacement = None
		self.early_accumulated_distance = None
		self.late_accumulated_distance = None
		self.total_accumulated_distance = None

		self.binning = None
		self.pixel_size = None
		self.dimensions = None
