import os
import couchdb
import hashlib
import time
import re
from glob import glob
from data_models import SessionData

import hotspur_setup


class SessionProcessor():

	admin_db_name = 'projects_overview'
	admin_overview_doc_name = 'projects_overview'
	user_overview_doc_name = 'sessions_overview'
	tracked_directories = []
	sessions = []
	session_databases = {}

	@classmethod
	def find_sessions(cls, search_globs):
		directories_to_track = []
		for search in search_globs:
			directories_to_track.extend(glob(search))

		for directory in directories_to_track:
			mdoc_files = glob('{}/*.mdoc'.format(directory))
			if len(mdoc_files) == 0:
				print('No mdoc files found. Skipping...')
				continue

			if directory not in cls.tracked_directories:
				print('Session found at {}'.format(directory))

				session, session_db = cls.create_new_session(directory)

				cls.sessions.append(session)
				cls.tracked_directories.append(directory)
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

		db, processing_dir = SessionProcessor.prepare_couchdb_database(user_id, sample_id, session_id)

		session_data = SessionData.read_from_couchdb_by_name(db)
		if session_data is None:
			print('No previous session data found. Generating...')
			session_data = SessionData()
			session_data.time = time.time()
			session_data.name = session_data.db_name = db.name
			session_data.session = session_id
			session_data.grid = sample_id
			session_data.user = user_id
			session_data.frames_directory = frames_directory
			session_data.processing_directory = processing_dir
			session_data.save_to_couchdb(db)
		else:
			print('Session data loaded from couchdb!')
		return session_data, db


	@staticmethod
	def get_db_name_hash(string_to_hash):
		string_to_hash = string_to_hash.encode('utf-8')
		m = hashlib.md5()
		m.update(string_to_hash)
		m.update(hotspur_setup.hash_salt.encode('utf-8'))
		return 'h' + m.hexdigest()

	@staticmethod
	def prepare_couchdb_database(user, grid, session):
		couch = couchdb.Server(hotspur_setup.couchdb_address)

		session_db_name = SessionProcessor.get_db_name_hash(user + grid + session)
		try:
			session_db = couch.create(session_db_name)
		except couchdb.http.PreconditionFailed:
			session_db = couch[session_db_name]

		user_db_name = SessionProcessor.get_db_name_hash(user)
		try:
			user_db = couch.create(user_db_name)
		except couchdb.http.PreconditionFailed:
			user_db = couch[user_db_name]
		try:
			doc = user_db[SessionProcessor.user_overview_doc_name]
		except:
			doc = {'_id': SessionProcessor.user_overview_doc_name}
		session_name = "{}_{}".format(grid, session)
		doc[session_name] = session_db_name
		user_db[SessionProcessor.user_overview_doc_name] = doc

		try:
			admin_db = couch.create(SessionProcessor.admin_db_name)
		except couchdb.http.PreconditionFailed:
			admin_db = couch[SessionProcessor.admin_db_name]
		try:
			doc = admin_db[SessionProcessor.admin_overview_doc_name]
		except:
			doc = {'_id': SessionProcessor.admin_overview_doc_name}
		doc[user] = user_db_name
		admin_db[SessionProcessor.admin_overview_doc_name] = doc

		# Make necessary directories
		processing_dir = "{}/{}/{}".format(hotspur_setup.projects_hashes_path, user_db_name, session_db_name)
		if not os.path.exists(processing_dir):
			os.makedirs(processing_dir)

		link_parent_dir = "{}/{}".format(hotspur_setup.projects_links_path, user)
		if not os.path.exists(link_parent_dir):
			os.makedirs(link_parent_dir)

		link = "{}/{}_{}".format(link_parent_dir, grid, session)
		if not os.path.exists(link):
			os.symlink(processing_dir, link)

		return session_db, processing_dir