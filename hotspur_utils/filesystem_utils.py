import re
from pathlib import Path

from hotspur_config import get_config
from hotspur_utils import hash_utils

from data_models import SessionData


def extract_session_from_path(frames_dir,match_string):
    regexp_string = create_regexp_from_match_string(match_string)
    p = re.compile(regexp_string)
    m = p.match(frames_dir)
    
    project_name = m.group('project')
    sample_name = m.group('sample')
    session_name = m.group('session')
    frames_path = frames_dir

    session = SessionData()
    session.name = '{}--{}--{}'.format(project_name, sample_name, session_name)
    session.hash = hash_utils.get_hash(session.name)
    session.sample_name = sample_name
    session.project_name = project_name
    session.project_hash = hash_utils.get_hash(project_name)

    session.frames_directory = str(frames_path)
    session.processing_directory = ensure_session_dirs(session)

    return session

def ensure_session_dirs(session):
    base_path = Path(get_config().data_path)
    hash_path = base_path / "projects/hashed"
    link_path = base_path / "projects/links"

    processing_path = hash_path / session.project_hash / session.hash
    processing_path.mkdir(parents=True, exist_ok=True)

    parent_path = link_path / session.project_name
    parent_path.mkdir(parents=True, exist_ok=True)

    link = parent_path / session.name
    if not link.exists:
        link.symlink_to(processing_path, target_is_directory=True)

    return str(processing_path)

def create_glob_from_match_string(match_string):
    return match_string.format(project="*",sample="*",session="*")


def create_regexp_from_match_string(match_string):
    return match_string.format(project="(?P<project>[^/]+)",sample="(?P<sample>[^/]+)",session="(?P<session>[^/]+)")