import os
import couchdb
import hashlib
import time
import re
from glob import glob
from data_models import SessionData

import hotspur_setup
from hotspur_utils import couchdb_utils, filesystem_utils


class SessionProcessor():

    def __init__(self):
        self.tracked_directories = []
        self.sessions = []

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
                    continue

        return self.sessions

    def validate_session(self, directory):
        mdoc_files = glob('{}/*.mdoc'.format(directory))
        if len(mdoc_files) == 0:
            print('No mdoc files found. Skipping...')
            return False
        return True

    def create_new_session(self, frames_directory):
        try:
            session = filesystem_utils.extract_session_from_path(frames_directory)
            print("Successfully derived session from path {}".format(path))
        except Exception as e:
            print("Failed to create session from path {}".format(frames_directory))
            print(e)
            raise e

        session.db = couchdb_utils.get_db(session.hash)
        if not session.fetch(session.db):
            print('No previous session data found. Generating...')
            try:
                couchdb_utils.update_project_list(session)
                couchdb_utils.update_session_list(session)
                session.push(session.db)
                print('Session data loaded from couchdb!')
            except Exception as e:
                print('Failed to update database for session {}'.format(session.name))
                print(e)
                raise e

        return session
