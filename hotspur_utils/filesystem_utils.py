from pathlib import Path

from hotspur_config import get_config
from hotspur_utils import hash_utils

from data_models import SessionData


def extract_session_from_path(frames_path):
    project_name = frames_path.parts[-3]
    sample_name = frames_path.parts[-2]
    session_name = frames_path.parts[-1]

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
    hash_path = Path(get_config().base_path) / "projects/hashed"
    link_path = Path(get_config().base_path) / "projects/links"

    processing_path = hash_path / session.project_hash / session.hash
    processing_path.mkdir(parents=True, exist_ok=True)

    parent_path = link_path / session.project_name
    parent_path.mkdir(parents=True, exist_ok=True)

    link = parent_path / session.name
    link.symlink_to(processing_path, target_is_directory=True)

    return processing_dir
