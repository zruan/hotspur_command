import os

from hotspur_config import get_config
from hotspur_utils import hash_utils, couchdb_utils
from data_models import ProjectData


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
            print('  {}/web-view/project/{}'.format(
                get_config().base_url,
                data["hash"]
            ))


def show_hash(input):
    hash = hash_utils.get_hash(input)
    print(f'\n{hash}\n')


def show_project_info(project_name):
    project_hash = hash_utils.get_hash(project_name)
    db = couchdb_utils.fetch_db(project_hash)
    project = ProjectData()
    project.fetch(db)

    print('\n')
    print(f'{project_name}')
    print(f'{project_hash}')
    print(f'{get_config().base_url}/web-view/project/{project_hash}')

    print('\n')
    print("Sessions")
    print("------------------------------")
    if project.sessions is None:
        print('No sessions')
        return
    for name, hash in project.sessions.items():
        print(f'- {name}')
        print(f'  {hash}')
        print(f'  {get_config().base_url}/web-view/session/{hash}')
        print('\n')
