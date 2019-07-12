import os
import couchdb
import hashlib
import time
import re
from glob import glob
from data_models import SessionData

import hotspur_setup
from hotspur_utils import cdb_util, fs_util


class SessionProcessor():

    def __init__(self):
        tracked_directories = []
        sessions = []

    def find_sessions(self, search_globs):
        search_matches = []
        for search in search_globs:
            search_matches.extend(glob(search))

        new_matches = [
            match for match in search_matches if match not in self.tracked_directories]

        for directory in new_matches:
            print('Found potential session at {}'.format(directory))
            valid = self.validate_session(directory)

            if valid and directory not in self.tracked_directories:
                print('Session found at {}'.format(directory))
                try:
                    session = self.create_new_session(directory)
                    self.sessions.append(session)
                    self.tracked_directories.append(directory)
                except:
                    print('Failed to create new session. Skipping...')
                    continue

        return sessions

    def validate_session(directory):
        mdoc_files = glob('{}/*.mdoc'.format(directory))
        if len(mdoc_files) == 0:
            print('No mdoc files found. Skipping...')
            return False
        else
        return True

    def create_new_session(self, frames_directory):
        session = fs_util.extract_session_from_path(frames_directory)

        cdb_util.update_project_list(session)
        cdb_util.update_session_list(session)

        session.db = cdb.get_db(session.hash)

        session_data = SessionData.read_from_couchdb_by_name(session.db)
        if session_data is None:
            print('No previous session data found. Generating...')
            session_data = SessionData()
            session_data.time = time.time()
            session_data.name = session.hash
            session_data.session = session.name
            session_data.grid = session.sample_name
            session_data.user = session.project_name
            session_data.frames_directory = frames_directory

            processing_directory = fs_util.ensure_processing_directory(session)
            session_data.processing_directory = processing_directory
            session_data.save_to_couchdb(session.db)
        else:
            print('Session data loaded from couchdb!')
        session.data = session_data

        return session

    @staticmethod
    def prepare_couchdb_database(project_name, sample_name, session_name):

        user_db_name = SessionProcessor.get_db_name_hash(user)
        session_name = "{}_{}".format(grid, session)

        couchdb_manager.ensure_project_in_admin_db(p)

        return session_db, processing_dir
