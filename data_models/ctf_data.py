from data_models import DataModel

class CtfData(DataModel):

	def __init__(self, base_name):
		super().__init__(base_name)

		self.ctf_image_file = None
		self.ctf_image_preview_file = None
		self.ctf_log = None
		self.ctf_epa_log = None

		self.astigmatism_angle = None
		self.defocus_u = None
		self.defocus_v = None
		self.estimated_b_factor = None
		self.estimated_resolution = None
		self.cross_correlation = None

		self.measured_ctf = None
		self.measured_ctf_no_bg = None
		self.ctf_resolution_a = None
		self.ctf_theory = None

