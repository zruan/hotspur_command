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

    if args.config:
        show_config()
        return

    args.help_func()

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

def show_config():
    print("Hotspur base path set to {}".format(hotspur_setup.base_path))
    print("Couchdb url set to {}".format(hotspur_setup.couchdb_address))
    print("Search for patterns {}".format(hotspur_setup.search_globs))
    print("Using gpus {}".format(hotspur_setup.available_gpus))
    print("Using {} threads".format(hotspur_setup.available_cpus))
    print("Accepting sessions no older than {} days".format(hotspur_setup.session_max_age))