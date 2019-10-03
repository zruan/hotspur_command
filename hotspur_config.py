import yaml


config = None


def load_config(path):
    global config

    try:
        with open(path, 'r') as fp:
            config = yaml.safe_load(fp)
        validate_config(config)
        return config
    except Exception as e:
        print(e)
        raise e


def get_config():
    global config

    if config is None:
        raise Exception('Hotspur config has not been loaded')
    else:
        return config


def validate_config(config):
    return True


# def setup_from_environment():
#     global base_path
#     global search_globs
#     global couchdb_address
#     global server_name
#     global hash_salt
#     global available_gpus
#     global available_cpus
#     global session_max_age

#     if "HOTSPUR_PATH" in os.environ:
#         base_path = os.environ["HOTSPUR_PATH"]
#     else:
#         print("No value for HOTSPUR_PATH in environment")
#         sys.exit()

#     if 'HOTSPUR_SERVER_NAME' in os.environ:
#       server_name = os.environ['HOTSPUR_SERVER_NAME']
#     else:
#       server_name = os.environ['HOSTNAME']

#     if "HOTSPUR_ADMIN_NAME" in os.environ and "HOTSPUR_ADMIN_PASS" in os.environ:
#         couchdb_address = "http://{}:{}@{}/couchdb/".format(
#             os.environ["HOTSPUR_ADMIN_NAME"],
#             os.environ["HOTSPUR_ADMIN_PASS"],
#             server_name
#         )
#     else:
#         print("Must give both HOTSPUR_ADMIN_NAME and HOTSPUR_ADMIN_PASS")
#         sys.exit()

#     if "HOTSPUR_SEARCH_GLOBS" in os.environ:
#         search_globs = os.environ["HOTSPUR_SEARCH_GLOBS"].split(":")
#     else:
#         search_globs = []

#     hash_salt = os.getenv("HOTSPUR_HASH_SALT",
#                             "Please make me more secure")

#     if "HOTSPUR_GPUS" in os.environ:
#         available_gpus = [int(id)
#                             for id in os.environ["HOTSPUR_GPUS"].split(',')]
#     else:
#         available_gpus = [0]

#     available_cpus = int(os.getenv('HOTSPUR_THREADS', 2))

#     session_max_age = float(os.getenv('HOTSPUR_SESSION_MAX_AGE', 365))
