import os
import time

import hotspur_setup
from hotspur_utils import hash_utils

from data_models import SessionData

# path for projects and their sessions, using hashed names for anonymity
hash_path = hotspur_setup.base_path + "/projects/hashed"
# path for symlinks to sessions, with plaintext names. For admins to find things
link_path = hotspur_setup.base_path + "/projects/links"


def extract_session_from_path(frames_directory):
    frames_directory = os.path.abspath(frames_directory) + '/'
    session_directory = os.path.join(frames_directory, os.pardir)
    sample_directory = os.path.join(session_directory, os.pardir)
    project_directory = os.path.join(sample_directory, os.pardir)

    session_name = os.path.basename(os.path.normpath(session_directory))
    sample_name = os.path.basename(os.path.normpath(sample_directory))
    project_name = os.path.basename(os.path.normpath(project_directory))

    session = SessionData()
    session.time = time.time()
    session.end_time = session.time
    session.name = '{}--{}--{}'.format(project_name, sample_name, session_name)
    session.hash = hash_utils.get_hash(session.name)
    session.sample_name = sample_name
    session.project_name = project_name
    session.project_hash = hash_utils.get_hash(project_name)

    session.frames_directory = frames_directory
    session.processing_directory = ensure_session_dirs(session)

    return session

def ensure_session_dirs(session):
    processing_dir = "{}/{}/{}".format(hash_path, session.project_hash, session.hash)
    if not os.path.exists(processing_dir):
        os.makedirs(processing_dir)

    parent_dir = "{}/{}".format(link_path, session.project_name)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    link = "{}/{}".format(parent_dir, session.name)
    if not os.path.exists(link):
        os.symlink(processing_dir, link)

    return processing_dir
