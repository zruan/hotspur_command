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
		self.finished_files = []
		self.running_files = []
		self.ignored_files = []

	def run(self, db, session_data):
		tif_glob = os.path.join(session_data.frames_directory, '*.tif')
		tif_files = glob(tif_glob)

		for file in tif_files:
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

			data_model = self.process_frames_file(file)
			data_model.save_to_couchdb(db)

	def process_frames_file(self, frames_file):
		base_name = Path(frames_file).stem
		mdoc_file_path = '{}.mdoc'.format(frames_file)
		data_model = AcquisitionData(base_name)

		with open(mdoc_file_path, 'r') as mdoc:
			for line in mdoc.readlines():
				# key-value pairs are separated by ' = ' in mdoc files
				if not ' = ' in line:
					continue
				key, value = [item.strip() for item in line.split(' = ')]
				# DEBUG print("Key: '{}'".format(key), "Value: '{}'".format(value))
				if key == 'Voltage':
					data_model.voltage = value
				elif key == 'ExposureDose':
					data_model.total_dose = value
				elif key == "ExposureTime":
					data_model.exposure_time = value
				elif key == 'PixelSpacing':
					data_model.pixel_size = value
				elif key == 'Binning':
					data_model.binning = value
				elif key == 'FrameDosesAndNumber':
					data_model.frame_count = value.split()[-1]
				elif key == 'GainReference':
					data_model.gain_reference_name = value
		return data_model
