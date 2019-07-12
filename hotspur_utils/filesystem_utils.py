import hotspur_setup
import hotspur_utils.hash_util

# path for projects and their sessions, using hashed names for anonymity
hash_path = hotspur_setup.base_path + "/projects/hashed"
# path for symlinks to sessions, with plaintext names. For admins to find things
link_path = hotspur_setup.base_path + "/projects/links"


def extract_session_from_path(path):
    frames_directory = os.path.abspath(frames_directory) + '/'
    session_directory = os.path.join(frames_directory, os.pardir)
    sample_directory = os.path.join(session_directory, os.pardir)
    project_directory = os.path.join(sample_directory, os.pardir)

    session_name = os.path.basename(os.path.normpath(session_directory))
    sample_name = os.path.basename(os.path.normpath(sample_directory))
    project_name = os.path.basename(os.path.normpath(project_directory))

    session = {
        name = session_name,
        hash = hash_util.get_hash(project_name, sample_name, session_name),
        sample_name = sample_name,
        project_name = project_name,
        project_hash = hash_util.get_hash(project_name)
    }

    ensure_session_dirs(session)

    return session


def ensure_session_dirs(session):
    processing_dir = "{}/{}/{}".format(hash_path, session.project_hash, session.hash)
    if not os.path.exists(processing_dir):
        os.makedirs(processing_dir)

    parent_dir = "{}/{}".format(link_path, session.project_name)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    link = "{}/{}_{}".format(parent_dir, session.sample_name, session.name)
    if not os.path.exists(link):
        os.symlink(processing_dir, link)

    return processing_dir
