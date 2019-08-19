import hotspur_setup
from processors import SessionProcessor
from hotspur_utils import hash_utils

def show_info(args):
    if args.hash is not None:
        show_hash(args.hash)
        return

    if args.project is not None:
        show_project_info(args.project)
        return

    session_processor = SessionProcessor()

    if args.dirs is not None:
        for session in session_processor.find_sessions(args.dirs):
            try:
                show_session_info(session)
            except:
                continue
        return

    if args.search:
        for session in session_processor.find_sessions(hotspur_setup.search_globs):
            try:
                show_session_info(session)
            except:
                continue
        return

    help_func()

def show_hash(input):
    hash = hash_utils.get_hash(input)
    print('Hash for input "{}" is:\n{}'.format(input, hash))

def show_project_info(project_name):
    print("Not yet implemented")

def show_session_info(session):
    print("Not yet implemented")