import os
from pathlib import Path
import sys
import time
from glob import glob
import tifffile
import numpy as np

from data_models import AcquisitionData
from processors import SessionProcessor


class FramesFileProcessor():

	# amount of time to wait before acting on a file. Prevents reading a partial file.
	_min_lifetime = 120

	def __init__(self):
		self.tracked_files_by_db = {}

	def run(self, session_data):
		db = SessionProcessor.get_couchdb_database(session_data.user, session_data.grid, session_data.session)
		if session_data not in self.tracked_files_by_db.keys():
			self.tracked_files_by_db[db.name] = self.load_from_couchdb(db)

		tif_glob = os.path.join(session_data.frames_directory, '*.tif')
		tif_files = glob(tif_glob)
		mrc_glob = os.path.join(session_data.frames_directory, '*.mrc')
		mrc_files = glob(mrc_glob)

		files = tif_files + mrc_files

		for file in files:
			base_name = os.path.basename(os.path.splitext(file)[0])
			if base_name in self.tracked_files_by_db[db.name]:
				continue

			acquisition_time = os.path.getmtime(file)
			current_time = time.time()
			file_lifetime = current_time - acquisition_time
			if file_lifetime < FramesFileProcessor._min_lifetime:
				continue

			mdoc_file = '{}.mdoc'.format(file)
			if not os.path.exists(mdoc_file):
				self.tracked_files_by_db[db.name].append(file)
				continue

			data_model = AcquisitionData(base_name)
			data_model.image_path = file
			data_model.file_format = os.path.splitext(file)[1]
			data_model.time = acquisition_time

			data_model = FramesFileProcessor.update_model_from_mdoc(mdoc_file, data_model, session_data)
			# data_model = FramesFileProcessor.update_dose_from_image(data_model.image_path, data_model)

			data_model.save_to_couchdb(db)
			self.tracked_files_by_db[db.name].append(file)

	@staticmethod
	def update_model_from_mdoc(mdoc_file_path, data_model, session_data):
		with open(mdoc_file_path, 'r') as mdoc:
			for line in mdoc.readlines():
				# key-value pairs are separated by ' = ' in mdoc files
				if not ' = ' in line:
					continue
				key, value = [item.strip() for item in line.split(' = ')]
				# DEBUG print("Key: '{}'".format(key), "Value: '{}'".format(value))
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
						session_data.frames_directory, value)
		return data_model

	@staticmethod
	def update_dose_from_image(file, data_model):
		with tifffile.TiffFile(file) as imfile:
			array = imfile.asarray()
			mean = np.mean(array)

		pixel_dose_rate = mean
		pixel_area = data_model.pixel_size ** 2
		area_dose_rate = pixel_dose_rate / pixel_area

		data_model.total_dose = area_dose_rate * data_model.exposure_time
		data_model.frame_dose = data_model.total_dose / data_model.frame_count
		
		return data_model

	def load_from_couchdb(self, db):
		return [item.base_name for item in AcquisitionData.find_docs_by_time(db)]
