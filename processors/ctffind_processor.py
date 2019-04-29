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
from hotspur_initialize import get_couchdb_database
from resource_manager import ResourceManager


class CtffindProcessor():

	def __init__(self):
		self.tracked_docs = []
		self.queued_listings = []
		self.finished_docs = []
		self.required_cpus = 1

	def run(self, session_data):
		db = get_couchdb_database(session_data.user, session_data.grid, session_data.session)

		# motion_correction_data_docs = MotionCorrectionData.find_docs_by_time(db)
		# self.finished_docs = [doc.base_name for doc in motion_correction_data_docs]

		motion_correction_data_docs = MotionCorrectionData.find_docs_by_time(db)
		for doc in motion_correction_data_docs:
			if doc.base_name in self.tracked_docs:
				continue
			else:
				self.tracked_docs.append(doc.base_name)
				# if doc.base_name not in self.finished_docs:
				self.queued_listings.append(doc)
				self.queued_listings.sort(key=lambda doc: doc.time)

		if len(self.queued_listings) == 0:
			return

		if ResourceManager.request_cpus(self.required_cpus):
			target_base_name = self.queued_listings.pop().base_name
			acquisition_data = AcquisitionData.read_from_couchdb_by_name(db, target_base_name)
			motion_correction_data = MotionCorrectionData.read_from_couchdb_by_name(db, target_base_name)
			process_thread = Thread(
				target=self.process_data,
				args=(session_data, acquisition_data, motion_correction_data)
			)
			process_thread.start()

	def process_data(self, session, acquisition_data, motion_correction_data):
		if motion_correction_data.dose_weighted_image_file is not None:
			image_file = motion_correction_data.dose_weighted_image_file
		else:
			image_file = motion_correction_data.aligned_image_file

		# Ctffind requires a HEREDOC. Yikes.
		command_list = [
			'ctffind << EOF',
			image_file,
			'{}.ctffind.ctf'.format(image_file),
			'{}'.format(motion_correction_data.pixel_size), # pixelsize
			# '{}'.format(acquisition_data.voltage), # acceleration voltage
			'300',
			'2.70', # Cs
			'0.1', # amplitude contrast
			'512', # size of amplitude spectrum to compute
			'20', # min resolution
			'4', # max resolution
			'5000', # min defocus
			'50000', # max defoxus
			'500', # defocus search step
			'no', # is astig known
			'yes', # slower, more exhaustive search
			'yes', # use a restraint on astig
			'200.0', # expected (tolerated) astig
			'no', # find additional phase shift
			'no', # set expert options
			'EOF'
		]

		subprocess.call('\n'.join(command_list), shell=True)
		ResourceManager.release_cpus(self.required_cpus)

	# 	data_model = MotionCorrectionData(acquisition_data.base_name)
	# 	data_model.aligned_image_file = output_file

	# 	if os.path.exists(output_file_dose_weighted):
	# 		data_model.dose_weighted_image_file = output_file_dose_weighted
	# 		preview_file = self.create_preview(output_file_dose_weighted)
	# 	else:
	# 		preview_file = self.create_preview(output_file)
	# 	data_model.preview_file = preview_file

	# 	shifts, initial_shift, total_shift = self.extract_shifts_from_log(output_log_file)
	# 	data_model.shift_list = shifts
	# 	data_model.initial_shift = initial_shift
	# 	data_model.total_shift = total_shift

	# 	dimensions, pixel_size = self.parse_mrc(output_file)
	# 	data_model.dimensions = dimensions
	# 	data_model.pixel_size = pixel_size

	# 	db = get_couchdb_database(session.user, session.grid, session.session)
	# 	data_model.save_to_couchdb(db)

	# 	self.finished_docs.append(data_model.base_name)

	# def create_preview(self, file):
	# 	image = imaging.load(file)[0]
	# 	image = imaging.filters.norm(image, 0.01, 0.01, 0, 255)
	# 	image = imaging.filters.zoom(image, 0.25)
	# 	preview_file = '{}.preview.png'.format(file)
	# 	imaging.save(image, preview_file)
	# 	return preview_file

	# def extract_shifts_from_log(self, output_log_file):
	# 	try:
	# 		with open(output_log_file, "r") as fp:
	# 			x_shifts = y_shifts = []
	# 			reading_shifts = False
	# 			for line in fp:
	# 				if reading_shifts:
	# 					if 'shift:' in line:
	# 						x_shift, y_shift = line.split()[-2:]
	# 						x_shifts.append(float(x_shift))
	# 						y_shifts.append(float(y_shift))
	# 					else:
	# 						reading_shifts = False
	# 				elif 'Full-frame alignment shift' in line:
	# 					reading_shifts = True
	# 			shifts = list(zip(x_shifts, y_shifts))
	# 			# use second element because first element is always zero
	# 			initial_shift = math.sqrt(x_shifts[1]**2 + y_shifts[1]**2)
	# 			total_shift = math.sqrt(sum(x_shifts)**2 + sum(y_shifts)**2)
	# 			return shifts, initial_shift, total_shift
	# 	except IOError:
	# 		print("No log found")
	# 		return None

	# def parse_mrc(self, file):
	# 	try:
	# 		header = imaging.formats.FORMATS["mrc"].load_header(file)
	# 		dimensions = (int(header['dims'][0]), int(header['dims'][1]))
	# 		pixel_size = float(header['lengths'][0]/header['dims'][0])
	# 		return dimensions, pixel_size
	# 	except AttributeError as e:
	# 		print(e)
	# 	except IOError:
	# 		print("Error loading mrc!", sys.exc_info()[0])

	# @staticmethod
	# def prepare_gain_reference(processing_directory, gain_file):
	# 	target_filename = "gainRef.mrc"
	# 	ext = os.path.splitext(gain_file)[1]
	# 	target_path = os.path.join(processing_directory, target_filename)

	# 	if not os.path.exists(target_path):
	# 		if ext == '.mrc':
	# 			os.system("cp {} {}".format(gain_file, target_path))
	# 		elif ext == '.dm4':
	# 			os.system("dm2mrc {} {}".format(gain_file, target_path))
	# 		else:
	# 			raise ValueError('Gain reference is not ".dm4" or ".mrc" format.')

	# 	return target_path
