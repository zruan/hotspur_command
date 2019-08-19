import hotspur_setup
from hotspur_utils.couchdb_utils import couchdb_server, fetch_db, fetch_doc, push_doc
from hotspur_utils import hash_utils
from processors import SessionProcessor

def reset(args):
    if args.all:
        reset_all()
        return
    
    if args.project is not None:
        reset_project(args.project)
        return

    session_process = SessionProcessor()

    if args.search:
        for session in session_processor.find_sessions(hotspur_setup.search_globs):
            try:
                reset_session(session)
            except:
                continue

    if args.dirs is not None:
        for session in session_processor.find_sessions(args.dirs):
            try:
                reset_session(session)
            except:
                continue
        return

    print(args)
    args.help_func()


def reset_all():
    for db_name in couchdb_server:
        # don't delete couchdb magic databases
        if db_name[0] != '_':
            try:
                couchdb_server.delete(db_name)
                print("Deleted database {}".format(db_name))
            except Exception as e:
                print(e)
                print("Failed to delete database {}".format(db_name))

def reset_project(project_name):
    project_hash = hash_utils.get_hash(project_name)
    try:
        db = fetch_db(project_hash)
        doc = fetch_doc(session_list_doc_name, db)
        if doc is None:
            raise Exception()
    except:
        print('Failed to retrieve list of sessions')
        return

    all_sessions_reset = True
    for key, val in doc.items():
        if key in ['_id', '_rev']:
            continue

        session_name = key
        session_hash = val

        try:
            couchdb_server.delete(session_hash)
            print('Deleted session database {}'.format(session_hash))
        except:
            all_sessions_reset = False
            continue

        try:
            db = fetch_db(project_hash)
            doc = fetch_doc(session_list_doc_name, db)
            del doc[session_name]
            push_doc(doc, db)
            print('Removed {} from session list for project {}'.format(session_name, project_name))
        except Exception as e:
            print('Failed to remove {} from session list for project {}'.format(session_name, project_name))
            print(e)
            raise e

    if not all_sessions_reset:
        print("Not all sessions deleted. Leaving project database")
        return

    try:
        couchdb_server.delete(project_hash)
        print("Deleted project database {}".format(project_hash))
    except:
        print("Failed to delete project database {}".format(project_hash))
        return

    try:
        db = fetch_db(admin_db_name)
        doc = fetch_doc(project_list_doc_name, db)
        del doc[project_name]
        push_doc(doc, db)
        print('Removed {} from project list'.format(project_name))
    except:
        print('Failed to remove {} from project list'.format(project_name))
        return

    return

def reset_session(session):
    try:
        couchdb_server.delete(session.hash)
        print('Deleted session database {}'.format(session.hash))
    except Exception as e:
        print('Failed to delete session database {}'.format(session.hash))
        print(e)
        raise e

    try:
        db = fetch_db(session.project_hash)
        doc = fetch_doc(session_list_doc_name, db)
        del doc[session.name]
        push_doc(doc, db)
        print('Removed {} from session list for project {}'.format(session.name, session.project_name))
    except Exception as e:
        print('Failed to remove {} from session list for project {}'.format(session.name, session.project_name))
        print(e)
        raise e
