import sys
import os
import time
import re
from glob import glob
from pathlib import Path
from types import SimpleNamespace

from hotspur_config import get_config

from hotspur_utils.logging_utils import get_logger_for_module
from hotspur_utils.couchdb_utils import fetch_db
from hotspur_utils import hash_utils

from data_models import SessionData


logger = get_logger_for_module(__name__)

class SessionProcessor():

    def __init__(self):
        self.tracked = []
        self.queued = []
        self.sessions = []


    def find_sessions(self, search_patterns):
        sessions = self.find_potential_sessions(search_patterns)
        logger.debug(f'Found new sessions')
        new_sessions = self.filter_for_untracked_sessions(sessions)
        self.track_and_queue_new_sessions(new_sessions)
        valid_sessions = self.get_valid_sessions_from_queue()

        for session in valid_sessions:
            try:
                self.ensure_processing_directory(session)
                self.link_processing_directory(session)
                session.db = fetch_db(session.hash)
                session.fetch(session.db)
                session.push(session.db)
                logger.debug(f'Pushed session {session.name} to couchdb')
                self.sessions.append(session)
                self.queued.remove(session)
            except Exception as e:
                logger.exception(e)
                continue


    def find_potential_sessions(self, search_patterns):
        found_sessions = []
        for pattern in search_patterns:
            glob_string = self.create_glob_from_pattern(pattern)
            session_directories = glob(glob_string)
            if len(session_directories) == 0:
                logger.debug(f"No session directories found using: {pattern}")
            sessions = [self.model_session(d, pattern) for d in session_directories]
            found_sessions.extend(sessions)
        return found_sessions


    def create_glob_from_pattern(self, pattern):
        return pattern.format(project="*",sample="*",session="*")


    def model_session(self, directory, pattern):
        parsed_names = self.parse_directory_path_for_names(directory, pattern)

        session = SessionData()
        # double cast for consistent path string formatting
        session.directory = str(Path(directory))
        session.name = '{}--{}--{}'.format(
            parsed_names.project_name,
            parsed_names.sample_name,
            parsed_names.session_name
        )
        session.sample_name = parsed_names.sample_name
        session.project_name = parsed_names.project_name
        session.hash = hash_utils.get_hash(session.name)
        session.project_hash = hash_utils.get_hash(session.project_name)
        return session


    def parse_directory_path_for_names(self, directory, pattern):
        regexp_string = pattern.format(
            project="(?P<project>[^/]+)",
            sample="(?P<sample>[^/]+)",
            session="(?P<session>[^/]+)"
        )
        regexp = re.compile(regexp_string)
        match = regexp.match(directory)
        return SimpleNamespace(
            project_name = match.group('project'),
            sample_name = match.group('sample'),
            session_name = match.group('session')
        )


    def filter_for_untracked_sessions(self, sessions):
        return [s for s in sessions if s.hash not in self.tracked]


    def track_and_queue_new_sessions(self, sessions):
        self.tracked.extend([s.hash for s in sessions])
        self.queued.extend(sessions)


    def get_valid_sessions_from_queue(self):
        return [s for s in self.queued if self.validate_session(s)]


    def validate_session(self, session):
        age = self.get_directory_age(session.directory)
        if age > get_config().session_max_age:
            logger.debug(f"Session {session.name} is not valid: age {age} is too old")
            return False

        if not self.contains_mdoc_file(session.directory):
            logger.debug(f"Session {session.name} is not valid: no mdoc file found")
            return False

        logger.debug(f"Session {session.name} is valid")
        return True


    def get_directory_age(self, directory):
        last_activity = os.path.getmtime(directory)
        current_time = time.time()
        age_in_seconds = current_time - last_activity
        age_in_days = age_in_seconds / (60 * 60 * 24)
        logger.debug(f'Age for {directory} is {age_in_days}')
        return age_in_days


    def contains_mdoc_file(self, directory):
        mdoc_files = glob(f'{directory}/*.mdoc')
        logger.debug(f'Found {len(mdoc_files)} in {directory}')
        return len(mdoc_files) > 0


    def ensure_processing_directory(self, session):
        processing_dir = self.get_processing_directory(session)
        logger.debug(f'Ensuring processing directory {processing_dir}')
        processing_dir.mkdir(parents=True, exist_ok=True)


    def link_processing_directory(self, session):
        processing_dir = self.get_processing_directory(session)

        link_dir = self.get_link_directory(session)
        logger.debug(f'Ensuring link directory {link_dir}')
        link_dir.mkdir(parents=True, exist_ok=True)

        link = link_dir / session.name
        if not link.exists:
            logger.debug(f'Creating link {link} to {processing_dir}')
            link.symlink_to(processing_dir, target_is_directory=True)


    def get_processing_directory(self, session):
        base_path = Path(get_config().data_path)
        hash_path = base_path / "projects/hashed"
        return hash_path / session.project_hash / session.hash


    def get_link_directory(self, session):
        base_path = Path(get_config().data_path)
        link_path = base_path / "projects/links"
        return link_path / session.project_name
