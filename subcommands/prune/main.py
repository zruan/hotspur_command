from utils.config import get_config
from utils.couchdb import couchdb_server, fetch_db
from utils.hash import get_hash
from utils.logging import get_logger_for_module
from data_models import SessionData, ProjectData


logger = get_logger_for_module(__name__)

def run(args):
    if args.all:
        reset_all()
        return

    if args.project is not None:
        reset_project(args.project)
        return

    if args.session is not None:
        reset_session(args.session)
        return

    logger.debug(args)
    args.help_func()


def reset_all():
    for db_name in couchdb_server:
        # don't delete couchdb magic databases
        if db_name[0] != '_':
            try:
                couchdb_server.delete(db_name)
                logger.info(f"Deleted database {db_name}")
            except Exception as e:
                logger.info(f"Failed to delete database {db_name}")
                logger.exception(e)


def reset_project(project_name):
    project_hash = get_hash(project_name)
    if not project_hash in couchdb_server:
        logger.info(f"Didn't find database {project_hash} for project {project_name}")
        return

    project_db = fetch_db(project_hash)
    project_data = ProjectData()
    project_data.fetch(project_db)

    failure_occured = False
    for session_hash in project_data.sessions.values():
        try:
            reset_session(session_hash)
        except:
            failure_occured = True
    
    if not failure_occured:
        couchdb_server.delete(project_hash)
        logger.info(f'Deleted database {project_hash} for project {project_name}')
    else:
        logger.info(f'Did not delete project database due to remaining session databases.')


def reset_session(session_hash):
    if not session_hash in couchdb_server:
        logger.info(f"Didn't find session database {session_hash}")
        return

    session_db = fetch_db(session_hash)
    session_data = SessionData()
    session_data.fetch(session_db)

    project_hash = get_hash(session_data.project_name)
    project_db = fetch_db(project_hash)
    project_data = ProjectData()
    project_data.fetch(project_db)
    del project_data.sessions[session_data.name]
    project_data.push(project_db)

    try:
        couchdb_server.delete(session_hash)
        logger.info(f'Deleted session database {session_hash}')
    except Exception as e:
        logger.info(f'Failed to delete session database {session_hash}')
        logger.exception(e)
        raise(e)

    return
