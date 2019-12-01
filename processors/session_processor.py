import os
import time
from glob import glob
from pathlib import Path
from types import SimpleNamespace

from hotspur_config import get_config

from hotspur_utils.logging_utils import get_logger_for_module
from hotspur_utils.couchdb_utils import fetch_db
from hotspur_utils.hash_utils import get_hash

from data_models import SessionData


LOG = get_logger_for_module(__name__)

class SessionProcessor():

    def __init__(self):
        self.tracked = []
        self.queued = []
        self.sessions = []


    def find_sessions(self, search_patterns):
        sessions = self.find_potential_sessions(search_patterns)
        sessions = [s for s in sessions if s.hash not in self.tracked]
        self.tracked.extend([s.hash for s in sessions])
        self.queued.extend(sessions)
        sessions = [s for s in self.queued if self.validate_session(s)]

        for session in sessions:
            try:
                dir = self.ensure_processing_directory(session)
                session.processing_directory = str(dir)
                self.link_processing_directory(session)
                session.db = fetch_db(session.hash)
                session.fetch(session.db)
                session.push(session.db)
                LOG.debug(f'Pushed session {session.name} to couchdb')
                self.sessions.append(session)
                self.queued.remove(session)
            except Exception as e:
                LOG.exception(e)
                continue


    def find_potential_sessions(self, search_patterns):
        found_sessions = []
        for pattern in search_patterns:
            directories = glob(pattern.glob)
            if len(directories) == 0:
                LOG.debug(f"No session directories found using glob {pattern.glob}")
            sessions = [self.model_session(d, pattern.mask) for d in directories]
            found_sessions.extend(sessions)
        return found_sessions


    def model_session(self, directory, mask):
        names = self.parse_directory_path_for_names(directory, mask)

        session = SessionData()
        # double cast for consistent path string formatting
        session.directory = str(Path(directory))
        session.name = names.session
        session.long_name = '{}--{}--{}'.format(
            names.project,
            names.sample,
            names.session
        )
        session.hash = get_hash(session.long_name)
        session.sample = names.sample
        session.project = names.project
        return session


    def parse_directory_path_for_names(self, directory, mask):
        d = Path(directory)
        m = Path(mask)
        if len(d.parts) != len(m.parts):
            raise Exception('Session directory path and mask are not the same length')

        names = SimpleNamespace()
        for i in range(len(d.parts)):
            if m.parts[i] == 'project':
                names.project = d.parts[i]
            elif m.parts[i] == 'sample':
                names.sample = d.parts[i]
            elif m.parts[i] == 'session':
                names.session = d.parts[i]

        return names


    def validate_session(self, session):
        age = self.get_directory_age(session.directory)
        if age > get_config().session_max_age:
            LOG.debug(f"Session {session.name} is not valid: age {age} is too old")
            return False

        if not self.contains_mdoc_file(session.directory):
            LOG.debug(f"Session {session.name} is not valid: no mdoc file found")
            return False

        LOG.debug(f"Session {session.name} is valid")
        return True


    def get_directory_age(self, directory):
        last_activity = os.path.getmtime(directory)
        current_time = time.time()
        age_in_seconds = current_time - last_activity
        age_in_days = age_in_seconds / (60 * 60 * 24)
        LOG.debug(f'Age for {directory} is {age_in_days}')
        return age_in_days


    def contains_mdoc_file(self, directory):
        mdoc_files = glob(f'{directory}/*.mdoc')
        LOG.debug(f'Found {len(mdoc_files)} in {directory}')
        return len(mdoc_files) > 0


    def ensure_processing_directory(self, session):
        processing_dir = self.get_processing_directory(session)
        LOG.debug(f'Ensuring processing directory {processing_dir}')
        processing_dir.mkdir(parents=True, exist_ok=True)
        return processing_dir


    def link_processing_directory(self, session):
        processing_dir = self.get_processing_directory(session)

        link_dir = self.get_link_directory(session)
        LOG.debug(f'Ensuring link directory {link_dir}')
        link_dir.mkdir(parents=True, exist_ok=True)

        link = link_dir / session.name
        if not link.exists:
            LOG.debug(f'Creating link {link} to {processing_dir}')
            link.symlink_to(processing_dir, target_is_directory=True)

        return link


    def get_processing_directory(self, session):
        base_path = Path(get_config().data_path)
        hash_path = base_path / "projects/hashed"
        return hash_path / session.hash


    def get_link_directory(self, session):
        base_path = Path(get_config().data_path)
        link_path = base_path / "projects/links"
        return link_path / session.project
