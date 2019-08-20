import hotspur_setup
from processors import SessionProcessor
from hotspur_utils import hash_utils, couchdb_utils

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
    project_hash = hash_utils.get_hash(project_name)
    db = couchdb_utils.fetch_db(project_hash)
    doc = couchdb_utils.fetch_doc(couchdb_utils.session_list_doc_name, db)

    print('\n')
    print("Project hash")
    print(project_hash)

    if doc is None:
        print("Did not find any sessions associated with this project")
        return

    print("Sessions")
    print("------------------------------")
    for key, val in doc.items():
        if key in ['_id', '_rev']:
            continue

        session_name = key
        session_hash = val
        print("{}   {}".format(session_hash, session_name))

def show_session_info(session):
    print("Not yet implemented")