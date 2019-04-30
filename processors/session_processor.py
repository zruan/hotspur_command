import os
import couchdb
from glob import glob
from data_models import SessionData

import hotspur_setup


class SessionProcessor():


	tracked_directories = {}
	sessions = []
	session_databases = {}

	@classmethod
	def find_sessions(cls, search_globs):
		directories_to_track = []
		for search in search_globs:
			directories_to_track.extend(glob(search))

		for directory in directories_to_track:
			if directory not in cls.tracked_directories.keys():
				session, session_db = cls.create_new_session(directory)
				cls.sessions.append(session)
				cls.tracked_directories[directory] = session
				cls.session_databases[session] = session_db
		return cls.sessions

	@classmethod
	def create_new_session(cls, frames_directory):
		frames_directory = os.path.abspath(frames_directory) + '/'
		session_directory = os.path.join(frames_directory, os.pardir)
		sample_directory = os.path.join(session_directory, os.pardir)
		user_directory = os.path.join(sample_directory, os.pardir)
	
		session_id = os.path.basename(os.path.normpath(session_directory))
		sample_id = os.path.basename(os.path.normpath(sample_directory))
		user_id = os.path.basename(os.path.normpath(user_directory))

		scratch_dir = "{}/{}/{}__{}/".format(hotspur_setup.base_path, user_id, sample_id, session_id)

		db = SessionProcessor.get_couchdb_database(user_id, sample_id, session_id)
		try:
			session_data = SessionData.read_from_couchdb_by_name(db)
		except:
			session_data = SessionData()
			session_data.session = session_id
			session_data.grid = sample_id
			session_data.user = user_id
			session_data.frames_directory = frames_directory
			session_data.processing_directory = scratch_dir
			session_data.save_to_couchdb(db)

		SessionProcessor.prepare_directory_structure(session_data)

		return session_data, db

	@staticmethod
	def prepare_directory_structure(session_data):
		if not os.path.exists(session_data.processing_directory):
			os.makedirs(session_data.processing_directory)

	@staticmethod
	def get_couchdb_database(user, grid, session):
		couch = couchdb.Server(hotspur_setup.couchdb_address)

		database_name = '_'.join(['hotspur', user, grid, session])
		database_name = database_name.lower()

		try:
			db = couch.create(database_name)
		except couchdb.http.PreconditionFailed:
			db = couch[database_name]

		return db