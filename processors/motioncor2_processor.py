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

	required_gpus = 1
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

		self.tracked = []
		self.queued = []
		self.finished = []

		self.sync_with_db()
	
	def sync_with_db(self):
		current_models = MotionCorrectionData.fetch_all(self.session.db)
		base_names = [model._id for model in current_models]
		self.tracked = base_names
		self.finished = base_names

	def update_tracked_data(self):
		current_models = AcquisitionData.fetch_all(self.session.db)
		for model in current_models:
			if model.base_name not in self.tracked:
				self.tracked.append(model.base_name)
				self.queued.append(model)
		self.queued.sort(key=lambda model: model.time)

	def run(self):
		self.update_tracked_data()

		if len(self.queued) == 0:
			return

		gpu_id_list = ResourceManager.request_gpus(Motioncor2Processor.required_gpus)
		if gpu_id_list is not None:
			try:
				acquisition_data_model = self.queued.pop()
				process_thread = Thread(
					target=self.process_data,
					args=(acquisition_data_model, gpu_id_list)
				)
				process_thread.start()
			except:
				ResourceManager.release_gpus(gpu_id_list)

	def process_data(self, acquisition_data_model, gpu_id_list):
		gain_file = self.prepare_gain_reference(
			self.session.processing_directory, acquisition_data_model.gain_reference_file
		)

		output_file_base = '{}/{}'.format(self.session.processing_directory, acquisition_data_model.base_name)
		output_file = '{}_mc.mrc'.format(output_file_base)
		output_file_dose_weighted = '{}_mc_DW.mrc'.format(output_file_base)
		output_log_file = '{}_mc.log'.format(output_file_base)

		command_list = [
			'motioncor2',
			'{} {}'.format('-InTiff' if acquisition_data_model.file_format == '.tif' else '-InMrc', acquisition_data_model.image_path),
			'-OutMrc {}'.format(output_file),
			'-Kv {}'.format(acquisition_data_model.voltage),
			'-gain {}'.format(gain_file),
			'-PixSize {}'.format(acquisition_data_model.pixel_size),
			'-FmDose {}'.format(acquisition_data_model.frame_dose),
			'-FtBin 2' if acquisition_data_model.binning == 0.5 else '',
			'-Iter 10',
			'-Tol 0.5',
			'-Gpu {}'.format(','.join([str(gpu_id) for gpu_id in gpu_id_list])),
			'> {}'.format(output_log_file)
		]
		subprocess.call(' '.join(command_list), shell=True)

		data_model = MotionCorrectionData(acquisition_data_model.base_name)
		data_model.time = time.time()
		data_model.aligned_image_file = output_file

		if os.path.exists(output_file_dose_weighted):
			data_model.dose_weighted_image_file = output_file_dose_weighted
			preview_file = self.create_preview(output_file_dose_weighted)
		else:
			preview_file = self.create_preview(output_file)
		data_model.preview_file = preview_file

		try:
			shifts, initial_shift, total_shift = self.extract_shifts_from_log(output_log_file)
			data_model.shift_list = shifts
			data_model.initial_shift = initial_shift
			data_model.total_shift = total_shift
		except Exception as e:
			print("Failed to extract shifts from log {}".format(output_log_file))
			print(e)

		try:
			dimensions, pixel_size = self.parse_mrc(output_file)
			data_model.dimensions = dimensions
			data_model.pixel_size = pixel_size
		except Exception as e:
			print("Failed to parse mrc header of {}".format(output_file))
			print(e)

		data_model.push(self.session.db)

		self.finished.append(data_model.base_name)

		ResourceManager.release_gpus(gpu_id_list)

	def create_preview(self, file):
		try:
			image = imaging.load(file)[0]
			image = imaging.filters.norm(image, 0.01, 0.01, 0, 255)
			image = imaging.filters.zoom(image, 0.25)
			preview_file = '{}.preview.png'.format(file)
			imaging.save(image, preview_file)
			return preview_file
		except Exception as e:
			print(e)
			return None

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
			raise e

	def parse_mrc(self, file):
		try:
			header = imaging.formats.FORMATS["mrc"].load_header(file)
			dimensions = (int(header['dims'][0]), int(header['dims'][1]))
			pixel_size = float(header['lengths'][0]/header['dims'][0])
			return dimensions, pixel_size
		except AttributeError as e:
			print(e)
			raise e
		except IOError as e:
			print("Error loading mrc!", sys.exc_info()[0])
			raise e

	def prepare_gain_reference(self, processing_directory, gain_file):
		target_filename = "gainRef.mrc"
		ext = os.path.splitext(gain_file)[1]
		target_path = os.path.join(processing_directory, target_filename)

		try:
			if not os.path.exists(target_path):
				if ext == '.mrc':
					os.system("cp {} {}".format(gain_file, target_path))
				elif ext == '.dm4':
					os.system("dm2mrc {} {}".format(gain_file, target_path))
				else:
					raise ValueError('Gain reference is not ".dm4" or ".mrc" format.')
			return target_path
		except Exception as e:
			print(e)
			raise e