import os
import time
from glob import glob
from threading import Lock, Thread
import subprocess
import imaging
import numpy as np

from data_models import AcquisitionData, MotionCorrectionData, CtfData 
from processors import SessionProcessor
from resource_manager import ResourceManager


class CtffindProcessor():

	def __init__(self):
		self.tracked_data = {}
		self.queued_listings = {}
		self.finished_docs = {}
		self.required_cpus = 1

	def run(self, session):
		if session.name not in self.tracked_data.keys():
			self.tracked_data[session.name] = []
		if session.name not in self.queued_listings.keys():
			self.queued_listings[session.name] = []
		if session.name not in self.finished_docs.keys():
			self.finished_docs[session.name] = []

		db = SessionProcessor.session_databases[session]

		ctf_data_summaries = CtfData.find_docs_by_time(db)
		self.finished_docs[session.name] = [doc.base_name for doc in ctf_data_summaries]

		motion_correction_data_docs = MotionCorrectionData.find_docs_by_time(db)
		for doc in motion_correction_data_docs:
			if doc.base_name not in self.tracked_data[session.name]:
				self.tracked_data[session.name].append(doc.base_name)
				if doc.base_name not in self.finished_docs:
					self.queued_listings[session.name].append(doc)
					self.queued_listings[session.name].sort(key=lambda doc: doc.time)

		if len(self.queued_listings[session.name]) == 0:
			return

		if ResourceManager.request_cpus(self.required_cpus):
			target_base_name = self.queued_listings[session.name].pop().base_name
			acquisition_data = AcquisitionData.read_from_couchdb_by_name(db, target_base_name)
			motion_correction_data = MotionCorrectionData.read_from_couchdb_by_name(db, target_base_name)
			process_thread = Thread(
				target=self.process_data,
				args=(session, acquisition_data, motion_correction_data)
			)
			process_thread.start()

	def process_data(self, session, acquisition_data, motion_correction_data):
		if motion_correction_data.dose_weighted_image_file is not None:
			aligned_image_file = motion_correction_data.dose_weighted_image_file
		else:
			aligned_image_file = motion_correction_data.aligned_image_file
		output_file_base = os.path.join(session.processing_directory, acquisition_data.base_name)
		output_file = '{}_ctffind.ctf'.format(output_file_base)

		# Ctffind requires a HEREDOC. Yikes.
		command_list = [
			'ctffind << EOF',
			aligned_image_file,
			output_file,
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

		data_model = CtfData(acquisition_data.base_name)
		data_model.time = time.time()
		data_model.ctf_image_file = output_file
		data_model.ctf_image_preview_file = self.create_preview(data_model.ctf_image_file)
		data_model.ctf_log_file = '{}_ctffind.txt'.format(output_file_base)
		data_model.ctf_epa_log_file = '{}_ctffind_avrot.txt'.format(output_file_base)

		data_model = self.update_model_from_EPA_log(data_model)
		data_model = self.update_model_from_ctffind_log(data_model)

		db = SessionProcessor.session_databases(session)
		_, doc_rev = data_model.save_to_couchdb(db)
		# data_model['_rev'] = doc_rev
		# with open(data_model.ctf_image_preview_file, 'rb') as fp:
		# 	db.put_attachment(data_model, fp, 'preview.png', 'image/png')

		self.finished_docs[session.name].append(data_model.base_name)

	def create_preview(self, file):
		image = imaging.load(file)[0]
		image = imaging.filters.norm(image, 0.01, 0.01, 0, 255)
		image = imaging.filters.zoom(image, 0.25)
		preview_file = '{}.preview.png'.format(file)
		imaging.save(image, preview_file)
		return preview_file

	def update_model_from_EPA_log(self, data_model):
		# ctffind4 log output filename: diagnostic_output_avrot.txt
		# columns:
		# 0 = spatial frequency (1/Angstroms)
		# 1 = 1D rotational average of spectrum (assuming no astigmatism)
		# 2 = 1D rotational average of spectrum
		# 3 = CTF fit
		# 4 = cross-correlation between spectrum and CTF fit
		# 5 = 2sigma of expected cross correlation of noise
		data = np.genfromtxt(
			data_model.ctf_epa_log_file,
			skip_header=5
		)
		# the first entry in spatial frequency is 0
		data[0] = np.reciprocal(data[0], where = data[0]!=0)
		data[0][0] = None
		data_model.measured_ctf_fit = list(np.nan_to_num(data[0]))
		data_model.measured_ctf = list(np.nan_to_num(data[2]))
		data_model.measured_ctf_no_bg = data_model.measured_ctf
		data_model.theoretical_ctf = list(np.nan_to_num(data[3]))
		# value["EPA"]["Ctffind_CC"] = list(np.nan_to_num(data[4]))
		# value["EPA"]["Ctffind_CCnoise"] = list(np.nan_to_num(data[5]))
		return data_model

	def update_model_from_ctffind_log(self, data_model):
		# ctffind output is diagnostic_output.txt
		# the last line has the non-input data in it, space-delimited
		# values:
		# 0: micrograph number; 1: defocus 1 (A); 2: defocus 2 (A); 3: astig azimuth;
		# 4: additional phase shift (radians); 5: cross correlation;
		# 6: spacing (in A) up to which CTF fit
		with open(data_model.ctf_log_file) as f:
			lines = f.readlines()
		ctf_params = lines[5].split(' ')
		data_model.defocus_u = (float(ctf_params[1]))
		data_model.defocus_v = (float(ctf_params[2]))
		data_model.astigmatism_angle = ctf_params[3]
		data_model.phase_shift = ctf_params[4]
		data_model.cross_correlation = ctf_params[5]
		data_model.estimated_resolution = ctf_params[6].rstrip()
		data_model.estimated_b_factor = 0
		return data_model