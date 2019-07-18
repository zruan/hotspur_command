import sys
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
        print (new_matches)
        self.tracked.extend(new_matches)
        self.queued.extend(new_matches)

        for directory in self.queued:
            print('Found potential session at {}'.format(directory))
            if self.validate_session(directory):
                print("Session is valid")
                try:
                    session = self.create_new_session(directory)
                    self.sessions.append(session)
                    self.queued.remove(directory)
                except:
                    continue
            else:
                print("Session is not valid, skipping")

        return self.sessions

    def validate_session(self, directory):
        mdoc_files = glob('{}/*.mdoc'.format(directory))
        if len(mdoc_files) == 0:
            return False
        return True

    def create_new_session(self, frames_directory):
        try:
            session = filesystem_utils.extract_session_from_path(frames_directory)
            print("Created session metadata")
        except Exception as e:
            print("Failed to create session metadata")
            print(e)
            raise e

        session.db = couchdb_utils.fetch_db(session.hash)
        if not session.fetch(session.db):
            try:
                couchdb_utils.update_project_list(session)
                couchdb_utils.update_session_list(session)
                print('Added session to admin lists')
                session.push(session.db)
                print('Session added to database')
            except Exception as e:
                print('Failed to add session to database')
                print(e)
                raise e
        else:
            print('Updated session metadata from database')

        return session
