import sys
import os
import time
from glob import glob

import hotspur_setup
from hotspur_utils import filesystem_utils
from hotspur_utils.couchdb_utils import fetch_db, fetch_doc, push_doc


class SessionProcessor():

    def __init__(self):
        self.tracked = []
        self.queued = []
        self.sessions = []

    def find_sessions(self, search_globs):
        search_matches = []
        for search in search_globs:
            search_matches.extend(glob(search))

        if len(search_matches) == 0:
            print("No session search matches found")

        new_matches = [
            match for match in search_matches if match not in self.tracked]
        self.tracked.extend(new_matches)
        self.queued.extend(new_matches)

        for directory in self.queued:
            print('Found potential session at {}'.format(directory))
            try:
                session = self.create_new_session(directory)
                self.update_project_data(session)
                self.queued.remove(directory)
                self.sessions.append(session)
            except Exception as err:
                print(err)
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
            session.db = fetch_db(session.hash)
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

    def update_project_data(self, session):
        try:
            project_db = fetch_db(session.project_hash)
            doc = fetch_doc('project_data', project_db, True)
            if not 'sessions' in doc:
                doc['name'] = session.project_name
                doc['hash'] = session.project_hash
                doc['sessions'] = {session.name: session.hash}
                push_doc(doc, project_db)
                print(f'Create project data doc for project {session.project_name}')
                print(f'Added session {session.name} to session list')
            elif session.name in doc['sessions']:
                print('Session {} is already in session list for project {}'.format(
                    session.name, session.project_name))
            else:
                doc['sessions'][session.name] = session.hash
                push_doc(doc, project_db)
                print('Added session {} to session list for project {}'.format(
                    session.name, session.project_name))

        except Exception as e:
            print('Failed to add session {} to session list for project {}'.format(
                session.name, session.project_name))
            print(e)
            raise e
