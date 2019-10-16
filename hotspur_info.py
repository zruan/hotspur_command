import os

from hotspur_config import get_config
from hotspur_utils import hash_utils, couchdb_utils


def main(args):
    if args.all:
        show_all_projects()
        return

    if args.hash is not None:
        show_hash(args.hash)
        return

    if args.project is not None:
        show_project_info(args.project)
        return

    args.help_func()


def show_all_projects():
    for db_name in couchdb_utils.couchdb_server:
        # skip couchdb magic databases
        if db_name[0] == '_':
            continue
        db = couchdb_utils.couchdb_server[db_name]
        if 'project_data' in db:
            data = couchdb_utils.fetch_doc('project_data', db)
            print('- {}'.format(data['name']))
            print('  {} session(s)'.format(len(data['sessions'].keys())))
            print('  http://{}/web-view/projects/{}'.format(
                get_config().server_name,
                data["hash"]
            ))
            print('\n')


def show_hash(input):
    hash = hash_utils.get_hash(input)
    print('Hash for input "{}" is:\n{}'.format(input, hash))


def show_project_info(project_name):
    print('Collecting info for project {project_name}\n')

    project_hash = hash_utils.get_hash(project_name)
    db = couchdb_utils.fetch_db(project_hash)
    doc = couchdb_utils.fetch_doc('project_data', db)

    print('  {}/web-view/projects/{}'.format(
        get_config().base_url,
        project_hash
    ))

    if doc is None:
        print("Did not find any sessions associated with this project")
        return

    print("Sessions")
    print("------------------------------")
    for key, val in doc['sessions'].items():
        if key in ['_id', '_rev']:
            continue

        session_name = key
        session_hash = val
        print(f'- {session_name}')
        print('  {}/web-view/sessions/{}'.format(
            get_config().base_url,
            session_hash
        ))
