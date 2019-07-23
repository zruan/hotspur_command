import os
import time
import glob
import tifffile
import imaging

from data_models import AcquisitionData
from processors import SessionProcessor


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

		# amount of time to wait before acting on a file. Prevents reading a partial file.
		self.min_lifetime = 120
		self.file_patterns = ['*.tif', '*.mrc']

		self.tracked = []
		self.queued = []
		self.finished = []

		self.sync_with_db()

	def sync_with_db(self):
		docs = AcquisitionData.fetch_all(self.session.db)
		image_paths = [doc['image_path'] for doc in docs]
		self.tracked = image_paths
		self.finished = image_paths

	def update_tracked_data(self):

		found_files = []
		for pattern in self.file_patterns:
			search_pattern = os.path.join(self.session.frames_directory, pattern)
			found_files.extend(glob.glob(search_pattern))

		for file in found_files:

			# File has already been found
			if file in self.tracked:
				continue

			# File is not old enough
			acquisition_time = os.path.getmtime(file)
			current_time = time.time()
			file_lifetime = current_time - acquisition_time
			if file_lifetime < self.min_lifetime:
				continue

			self.tracked.append(file)
			self.queued.append(file)

	def run(self):
		self.update_tracked_data()

		for file in self.queued:
			# File doesn't have associated mdoc
			mdoc_file = '{}.mdoc'.format(file)
			if not os.path.exists(mdoc_file):
				self.queued.remove(file)
				self.finished.append(file)
				continue

			base_name = os.path.basename(os.path.splitext(file)[0])
			data_model = AcquisitionData(base_name)
			data_model.image_path = file
			data_model.file_format = os.path.splitext(file)[1]
			data_model.time = os.path.getmtime(file)
			data_model = self.update_model_from_mdoc(mdoc_file, data_model)
			data_model = self.update_dose_from_image(data_model)
			data_model.push(self.session.db)

			self.queued.remove(file)
			self.finished.append(file)

	def update_model_from_mdoc(self, mdoc_file_path, data_model):
		with open(mdoc_file_path, 'r') as mdoc:
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
					data_model.gain_reference_file = os.path.join(
						self.session.frames_directory, value
					)

		return data_model

	def update_dose_from_image(self, data_model):
		if data_model.file_format == '.tif':
			try:
				with tifffile.TiffFile(data_model.image_path) as imfile:
					frame_dose_per_pixel = imfile.pages[0].asarray().mean()
				print("Extracted dose rate from {}".format(data_model.image_path))
			except:
				print("Couldn't extract dose rate from {}".format(data_model.image_path))
				return data_model
		elif data_model.file_format == '.mrc':
			try:
				imfile = imaging.load(data_model.image_path)
				frame_dose_per_pixel = imfile.mean()
				print("Extracted dose rate from {}".format(file))
			except:
				print("Couldn't extract dose rate from {}".format(file))
				return data_model

		try:
			data_model.frame_dose = frame_dose_per_pixel / (data_model.pixel_size ** 2)
			data_model.total_dose = data_model.frame_dose * data_model.frame_count
			print("Populated dose rate fields in acquisition data")
		except Exception as e:
			print("Failed to populate dose rate fields in acquisition data")
			print(e)

		return data_model
