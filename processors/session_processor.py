import sys
import os
import time
from glob import glob

import hotspur_setup
from hotspur_utils import couchdb_utils, filesystem_utils


class SessionProcessor():

    def __init__(self):
        self.tracked = []
        self.queued = []
        self.sessions = []

    def find_sessions(self, search_globs):
        search_matches = []
        for search in search_globs:
            search_matches.extend(glob(search))

        new_matches = [
            match for match in search_matches if match not in self.tracked]
        self.tracked.extend(new_matches)
        self.queued.extend(new_matches)

        for directory in self.queued:
            print('Found potential session at {}'.format(directory))
            try:
                session = self.create_new_session(directory)
                couchdb_utils.update_session_list(session)
                couchdb_utils.update_project_list(session)
                self.sessions.append(session)
                self.queued.remove(directory)
            except:
                continue

        return self.sessions

    def validate_session(self, directory):
        mod_time = os.path.getmtime(directory)
        current_time = time.time()
        time_diff = current_time - mod_time
        time_diff_days = time_diff / (60 * 60 * 24)
        if time_diff_days > hotspur_setup.session_max_age:
            print("Session is not valid: age {} is too old".format(time_diff_days))
            return False

        mdoc_files = glob('{}/*.mdoc'.format(directory))
        if len(mdoc_files) == 0:
            print("Session is not valid: no mdoc file found")
            return False
        print("Session is valid")
        return True

    def create_new_session(self, frames_directory):
        if not self.validate_session(frames_directory):
            raise Exception()

        try:
            session = filesystem_utils.extract_session_from_path(frames_directory)
            print("Parsed session metadata")
        except Exception as e:
            print("Failed to parse session metadata")
            print(e)
            raise e

        try:
            session.db = couchdb_utils.fetch_db(session.hash)
        except Exception as e:
            print(e)
            raise e
            
        if not session.fetch(session.db):
            try:
                session.push(session.db)
                print('Session added to database')
            except Exception as e:
                print('Failed to add session to database')
                print(e)
                raise e
        else:
            print('Updated session metadata from database')

        return session
