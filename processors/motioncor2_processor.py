import os
from pathlib import Path
import sys
import time
import imaging
from glob import glob
from threading import Lock, Thread
import subprocess
import math

from data_models import AcquisitionData, MotionCorrectionData
from processors import SessionProcessor
from resource_manager import ResourceManager


class Motioncor2Processor():

	def __init__(self):
		self.tracked_data = {}
		self.queued_listings = {}
		self.finished_docs = {}
		self.required_gpus = 1

	def run(self, session):
		if session.name not in self.tracked_data.keys():
			self.tracked_data[session.name] = []
		if session.name not in self.queued_listings.keys():
			self.queued_listings[session.name] = []
		if session.name not in self.finished_docs.keys():
			self.finished_docs[session.name] = []

		db = SessionProcessor.session_databases[session]

		motion_correction_data_docs = MotionCorrectionData.find_docs_by_time(db)
		self.finished_docs[session.name] = [doc.base_name for doc in motion_correction_data_docs]

		acquisition_data_summaries = AcquisitionData.find_docs_by_time(db)
		for summary in acquisition_data_summaries:
			if summary.base_name not in self.tracked_data[session.name]:
				self.tracked_data[session.name].append(summary.base_name)
				if summary.base_name not in self.finished_docs[session.name]:
					self.queued_listings[session.name].append(summary)
					self.queued_listings[session.name].sort(key=lambda doc: doc.time)

		if len(self.queued_listings[session.name]) == 0:
			return

		gpu_id_list = ResourceManager.request_gpus(self.required_gpus)
		if gpu_id_list is not None:
			target_base_name = self.queued_listings[session.name].pop().base_name
			acquisition_data = AcquisitionData.read_from_couchdb_by_name(db, target_base_name)
			process_thread = Thread(target=self.process_data, args=(session, acquisition_data, gpu_id_list))
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

		data_model = MotionCorrectionData(acquisition_data.base_name)
		data_model.time = time.time()
		data_model.aligned_image_file = output_file

		if os.path.exists(output_file_dose_weighted):
			data_model.dose_weighted_image_file = output_file_dose_weighted
			preview_file = self.create_preview(output_file_dose_weighted)
		else:
			preview_file = self.create_preview(output_file)
		data_model.preview_file = preview_file

		shifts, initial_shift, total_shift = self.extract_shifts_from_log(output_log_file)
		data_model.shift_list = shifts
		data_model.initial_shift = initial_shift
		data_model.total_shift = total_shift

		dimensions, pixel_size = self.parse_mrc(output_file)
		data_model.dimensions = dimensions
		data_model.pixel_size = pixel_size

		db = SessionProcessor.get_couchdb_database(session.user, session.grid, session.session)
		_, doc_rev = data_model.save_to_couchdb(db)
		# data_model['_rev'] = doc_rev
		# with open(data_model.preview_file, 'rb') as fp:
		# 	db.put_attachment(data_model, fp, 'preview.png', 'image/png')

		self.finished_docs[session.name].append(data_model.base_name)

	def create_preview(self, file):
		image = imaging.load(file)[0]
		image = imaging.filters.norm(image, 0.01, 0.01, 0, 255)
		image = imaging.filters.zoom(image, 0.25)
		preview_file = '{}.preview.png'.format(file)
		imaging.save(image, preview_file)
		return preview_file

	def extract_shifts_from_log(self, output_log_file):
		try:
			with open(output_log_file, "r") as fp:
				x_shifts = []
				y_shifts = []
				reading_shifts = False
				for line in fp:
					if reading_shifts:
						if 'shift:' in line:
							columns = line.split()
							x_shifts.append(float(columns[-2]))
							y_shifts.append(float(columns[-1]))
						else:
							reading_shifts = False
					elif 'Full-frame alignment shift' in line:
						reading_shifts = True
				# use second element because first element is always zero
				initial_shift = math.sqrt(x_shifts[1]**2 + y_shifts[1]**2)
				total_shift = math.sqrt(sum(x_shifts)**2 + sum(y_shifts)**2)
				shifts = list(zip(x_shifts, y_shifts))
				return shifts, initial_shift, total_shift
		except IOError:
			print("No log found")
			return None

	def parse_mrc(self, file):
		try:
			header = imaging.formats.FORMATS["mrc"].load_header(file)
			dimensions = (int(header['dims'][0]), int(header['dims'][1]))
			pixel_size = float(header['lengths'][0]/header['dims'][0])
			return dimensions, pixel_size
		except AttributeError as e:
			print(e)
		except IOError:
			print("Error loading mrc!", sys.exc_info()[0])

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
