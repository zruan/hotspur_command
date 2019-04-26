from data_models import DataModel

class AcquisitionData(DataModel):

	def __init__(self, base_name):
		super().__init__(base_name)

		self.image_path = None
		self.base_name = None

		self.session_id = None
		self.grid_id = None
		self.proposal_id = None

		self.instrument = None
		self.voltage = None
		self.acquisition_time = None
		self.gain_reference_name = None
		self.gain_reference_path = None

		self.total_dose = None
		self.exposure_time = None
		self.frame_count = None
		self.pixel_size = None
		self.binning = None

		self.motion_correction_doc_id = None
		self.ctf_estimation_doc_id = None
