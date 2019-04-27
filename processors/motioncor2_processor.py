import os
from pathlib import Path
import sys
import time
from glob import glob
from threading import Lock, Thread
import subprocess

from data_models import AcquisitionData
from hotspur_initialize import get_couchdb_database
from resource_manager import ResourceManager


class Motioncor2Processor():

	def __init__(self):
		self.tracked_docs = []
		self.queued_listings = []
		self.required_gpus = 1

	def run(self, session_data):
		db = get_couchdb_database(session_data.user, session_data.grid, session_data.session)

		acquisition_data_docs = AcquisitionData.find_docs_by_time(db)
		for doc in acquisition_data_docs:
			if doc.base_name in self.tracked_docs:
				continue
			else:
				self.tracked_docs.append(doc.base_name)
				self.queued_listings.append(doc)
				self.queued_listings.sort(key=lambda doc: doc.time)

		if len(self.queued_listings) == 0:
			return

		gpu_id_list = ResourceManager.request_gpus(self.required_gpus)
		if gpu_id_list is not None:
			target_base_name = self.queued_listings.pop().base_name
			acquisition_data = AcquisitionData.read_from_couchdb_by_name(db, target_base_name)
			process_thread = Thread(target=self.process_data, args=(session_data, acquisition_data, gpu_id_list))
			process_thread.start()

	def process_data(self, session, acquisition_data, gpu_id_list):
		gain_file = Motioncor2Processor.prepare_gain_reference(session.processing_directory, acquisition_data.gain_reference_file)
		output_file_base = '{}{}'.format(session.processing_directory, acquisition_data.base_name)
		output_file = '{}_mc.mrc'.format(output_file_base)
		output_file_dose_weighted = '{}_mc_DW.mrc'.format(output_file_base)
		output_log_file = '{}_mc.log'.format(output_file_base)

		command_list = [
			'motioncor2',
			'{} {}'.format('-InTiff' if acquisition_data.file_format == '.tif' else '-InMrc', acquisition_data.image_path),
			'-OutMrc {}'.format(output_file),
			'-Kv {}'.format(acquisition_data.voltage),
			'-gain {}'.format(gain_file),
			'-PixSize {}'.format(acquisition_data.pixel_size),
			'-FmDose {}'.format(acquisition_data.frame_dose),
			'-FtBin 2' if acquisition_data.binning == 0.5 else '',
			'-Iter 10',
			'-Tol 0.5',
			'-Gpu {}'.format(','.join([str(gpu_id) for gpu_id in gpu_id_list])),
			'> {}'.format(output_log_file)
		]
		subprocess.call(' '.join(command_list), shell=True)
		ResourceManager.release_gpus(gpu_id_list)

		if os.path.exists(output_file_dose_weighted):
			subprocess.call(['rm', output_file])

	@staticmethod
	def prepare_gain_reference(processing_directory, gain_file):
		target_filename = "gainRef.mrc"
		ext = os.path.splitext(gain_file)[1]
		target_path = os.path.join(processing_directory, target_filename)

		if not os.path.exists(target_path):
			if ext == '.mrc':
				os.system("cp {} {}".format(gain_file, target_path))
			elif ext == '.dm4':
				os.system("dm2mrc {} {}".format(gain_file, target_path))
			else:
				raise ValueError('Gain reference is not ".dm4" or ".mrc" format.')

		return target_path








		# for file in files:
		# 	if file in self.tracked_files:
		# 		continue

		# 	acquisition_time = os.path.getmtime(file)
		# 	current_time = time.time()
		# 	file_lifetime = current_time - acquisition_time
		# 	if file_lifetime < FramesFileProcessor._min_lifetime:
		# 		continue

		# 	mdoc_file = '{}.mdoc'.format(file)
		# 	if not os.path.exists(mdoc_file):
		# 		self.tracked_files.append(file)
		# 		continue

		# 	base_name = Path(file).stem
		# 	mdoc_file_path = '{}.mdoc'.format(file)
		# 	data_model = AcquisitionData(base_name)
		# 	data_model.image_path = file
		# 	data_model.file_format = os.path.splitext(file)[0]
		# 	data_model.time = acquisition_time

		# 	with open(mdoc_file_path, 'r') as mdoc:
		# 		for line in mdoc.readlines():
		# 			# key-value pairs are separated by ' = ' in mdoc files
		# 			if not ' = ' in line:
		# 				continue
		# 			key, value = [item.strip() for item in line.split(' = ')]
		# 			# DEBUG print("Key: '{}'".format(key), "Value: '{}'".format(value))
		# 			if key == 'Voltage':
		# 				data_model.voltage = int(value)
		# 			elif key == 'ExposureDose':
		# 				data_model.total_dose = float(value)
		# 			elif key == "ExposureTime":
		# 				data_model.exposure_time = float(value)
		# 			elif key == 'PixelSpacing':
		# 				data_model.pixel_size = float(value)
		# 			elif key == 'Binning':
		# 				data_model.binning = float(value)
		# 			elif key == 'NumSubFrames':
		# 				data_model.frame_count = int(value)
		# 			elif key == 'GainReference':
		# 				data_model.gain_reference_file = os.path.join(
		# 					session_data.frames_directory, value)

		# 	data_model.save_to_couchdb(db)
		# 	self.tracked_files.append(file)
