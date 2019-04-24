import couchdb

class AcquisitionData():

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
		self.dose_rate = None
		self.pixel_size = None
		self.binning = None
		self.frame_count = None
		self.motion_correction_doc_id = None
		self.ctf_estimation_doc_id = None

	def save_to_couchdb(self, db):
		db.save(self.__dict__)

	@classmethod
	def read_from_mdoc(self, mdoc_file_path):
		params = AcquisitionData()
		with open(mdoc_file_path, 'r') as mdoc:
			for line in mdoc.readlines():
				# section headers start with a '[' so we skip them
				if line[0] == '[':
					continue
				if not ' = ' in line:
					continue
				key, value = [item.strip() for item in line.split(' = ')]
				# DEBUG print("Key: '{}'".format(key), "Value: '{}'".format(value))
				if key == 'Voltage':
					params.voltage = value
				elif key == 'ExposureDose':
					params.dose_rate = value
				elif key == 'PixelSpacing':
					params.pixel_size = value
				elif key == 'Binning':
					params.binning = value
				elif key == 'FrameDosesAndNumber':
					params.frame_count = value.split()[-1]
				elif key == 'GainReference':
					params.gain_reference_name = value

		return params

	@classmethod
	def read_from_couchdb(self, db, doc_id):
		params = AcquisitionData()
		params.__dict__ = db.load(doc_id)
		return params

if __name__ == "__main__":
	print(AcquisitionData.read_from_mdoc(
		"test_files/Grid6_1715.tif.mdoc").__dict__)
