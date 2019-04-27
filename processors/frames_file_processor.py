import os
from pathlib import Path
import sys
import time
from glob import glob

from data_models import AcquisitionData


class FramesFileProcessor():

	# amount of time to wait before acting on a file. Prevents reading a partial file.
	_min_lifetime = 120

	def __init__(self):
		self.tracked_files = []

	def run(self, db, session_data):
		tif_glob = os.path.join(session_data.frames_directory, '*.tif')
		tif_files = glob(tif_glob)
		mrc_glob = os.path.join(session_data.frames_directory, '*.mrc')
		mrc_files = glob(mrc_glob)

		files = tif_files + mrc_files

		for file in files:
			if file in self.tracked_files:
				continue

			acquisition_time = os.path.getmtime(file)
			current_time = time.time()
			file_lifetime = current_time - acquisition_time
			if file_lifetime < FramesFileProcessor._min_lifetime:
				continue

			mdoc_file = '{}.mdoc'.format(file)
			if not os.path.exists(mdoc_file):
				self.tracked_files.append(file)
				continue

			base_name = Path(file).stem
			mdoc_file_path = '{}.mdoc'.format(file)
			data_model = AcquisitionData(base_name)
			data_model.image_path = file
			data_model.file_format = os.path.splitext(file)[0]
			data_model.time = acquisition_time

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

			data_model.save_to_couchdb(db)
			self.tracked_files.append(file)
