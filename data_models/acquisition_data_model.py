import couchdb

class AcquisitionDataModel():

	def __init__(self):
		self._id = None
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

	def save_to_couchdb(self, db):
		db.save(self.__dict__)

	@staticmethod
	def read_from_couchdb_by_id(db, doc_id):
		params = AcquisitionDataModel()
		params.__dict__ = db.load(doc_id)
		return params

	@staticmethod
	def read_from_couchdb_by_name(db, base_name):
		id = AcquisitionDataModel.generate_id(base_name)
		return AcquisitionDataModel.read_from_couchdb_by_id(db, id)

	@staticmethod
	def generate_id(base_name):
		return base_name + '_movie'
