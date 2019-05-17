import os
from pathlib import Path
import sys
import time
from glob import glob
from io import StringIO
import struct
import tifffile
import numpy as np

from data_models import AcquisitionData
from processors import SessionProcessor


class FramesFileProcessor():

	# amount of time to wait before acting on a file. Prevents reading a partial file.
	_min_lifetime = 120
	_search_globs = ['*.tif', '*.mrc']

	def __init__(self):
		self.tracked_files = []

	def update_from_couchdb(self, session):
		db = SessionProcessor.session_databases[session]
		summaries = AcquisitionData.find_docs_by_time(db)
		for summary in summaries:
			doc = AcquisitionData.read_from_couchdb_by_name(db, summary.base_name)
			self.tracked_files.append(doc.image_path)

	def run(self, session):
		found_files = []
		for search in FramesFileProcessor._search_globs:
			search_path = os.path.join(session.frames_directory, search)
			found_files.extend(glob(search_path))

		for file in found_files:

			# File has already been found
			if file in self.tracked_files:
				continue

			# File is not old enough
			acquisition_time = os.path.getmtime(file)
			current_time = time.time()
			file_lifetime = current_time - acquisition_time
			if file_lifetime < FramesFileProcessor._min_lifetime:
				continue

			# File doesn't have associated mdoc
			mdoc_file = '{}.mdoc'.format(file)
			if not os.path.exists(mdoc_file):
				self.tracked_files.append(file)
				continue

			# File is new: prepare acquisition model
			base_name = os.path.basename(os.path.splitext(file)[0])
			data_model = AcquisitionData(base_name)
			data_model.image_path = file
			data_model.file_format = os.path.splitext(file)[1]
			data_model.time = acquisition_time

			data_model = FramesFileProcessor.update_model_from_mdoc(mdoc_file, data_model, session)
			# data_model = FramesFileProcessor.update_dose_from_image(data_model.image_path, data_model)

			db = SessionProcessor.session_databases[session]
			data_model.save_to_couchdb(db)
			self.tracked_files.append(file)

	@staticmethod
	def update_model_from_mdoc(mdoc_file_path, data_model, session_data):
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
						session_data.frames_directory, value)
		return data_model

	@staticmethod
	def update_dose_from_image(file, data_model):
		decompressed_file = FramesFileProcessor.decompress_lzw(file)
		with tifffile.TiffFile(decompressed_file) as imfile:
			array = imfile.asarray()
			mean = np.mean(array)

		pixel_dose_rate = mean
		pixel_area = data_model.pixel_size ** 2
		area_dose_rate = pixel_dose_rate / pixel_area

		data_model.total_dose = area_dose_rate * data_model.exposure_time
		data_model.frame_dose = data_model.total_dose / data_model.frame_count
		
		return data_model

	@staticmethod
	def decompress_lzw(file):
		compressed = []
		with open(file, 'rb') as fp:
			while True:
				rec = fp.read(2)
				if len(rec) != 2:
					break
				(data, ) = struct.unpack('>H', rec)
				compressed.append(data)
		# FROM https://rosettacode.org/wiki/LZW_compression#Python

		# Build the dictionary.
		dict_size = 256
		dictionary = {i: chr(i) for i in range(dict_size)}
	
		# use StringIO, otherwise this becomes O(N^2)
		# due to string concatenation in a loop
		result = StringIO()
		compressed = list(compressed)
		w = compressed.pop(0)
		result.write(w)


		for k in compressed:
			if k in dictionary:
				entry = dictionary[k]
			elif k == dict_size:
				entry = w + w[0]
			else:
				raise ValueError('Bad compressed k: %s' % k)
			result.write(entry)
	
			# Add w+entry[0] to the dictionary.
			dictionary[dict_size] = w + entry[0]
			dict_size += 1
	
			w = entry
		return result.getvalue()

	def load_from_couchdb(self, db):
		return [item.base_name for item in AcquisitionData.find_docs_by_time(db)]
