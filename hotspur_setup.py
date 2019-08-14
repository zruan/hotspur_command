import os
import sys

# directory hotspur uses for all its functionality
base_path = "/pncc/storage/1/processing/hotspur"

search_globs = [
    # '/pncc/storage/1/rawdata/pncc-testing/hotspur-tests/*/*/*/frames/',
    # '/pncc/storage/1/rawdata/pncc-testing/hotspur-tests/50633/20190429-asic-sma/screening-4/frames/',
    # '/goliath/rawdata/MMC/Confometrx/190618/0426-2_2/frames',
    '/pncc/storage/1/rawdata/pncc/*/*/*/frames/',
    # '/pncc/storage/1/rawdata/pncc/*/*/*/screen/',
    # '/pncc/storage/1/rawdata/pncc/*/*/*/',
    # '/pncc/storage/1/rawdata/pncc-testing/SEM_scripts/test_data_2/'
]

couchdb_address = "http://pncc:cryoem@localhost/couchdb/"
hash_salt = "feilivinglab-17"

available_gpus = [0, 1, 2, 3]
available_cpus = 12

# Maximum age of directory for valid session, in days.
# If mod time of directory is older, it will be skipped.
# Run `touch /path/to/dir` on the command line to refresh the mod time.
session_max_age = 7


def setup_from_environment():
    if "HOTSPUR_PATH" in os.environ:
        base_path = os.environ["HOTSPUR_PATH"]
        print("Hotspur base path set to {}".format(base_path))
    else:
        print("No value for HOTSPUR_PATH in environment")
        sys.exit()

    if "HOTSPUR_ADMIN_NAME" in os.environ and "HOTSPUR_ADMIN_PASS" in os.environ and ["HOTSPUR_COUCHDB_URL"]:
        couchdb_address = "http://{}:{}@{}".format(
            os.environ["HOTSPUR_ADMIN_NAME"],
            os.environ["HOTSPUR_ADMIN_PASS"],
            os.environ["HOTSPUR_COUCHDB_URL"]
        )
        print("Received couchdb url")
    else:
        print("Must give both HOTSPUR_ADMIN_NAME and HOTSPUR_ADMIN_PASS")
        sys.exit()

    if "HOTSPUR_SEARCH_GLOBS" in os.environ:
        search_globs = os.environ["HOTSPUR_SEARCH_GLOBS"].split(":")
    else:
        search_globs = []
    print("Search for patterns {}".format(search_globs))

    hash_salt = os.getenv("HOTSPUR_HASH_SALT",
                            "Please make me more secure")

    if "HOTSPUR_GPUS" in os.environ:
        available_gpus = [int(id)
                            for id in os.environ["HOTSPUR_GPUS"].split(',')]
    else:
        available_gpus = [0]
    print("Using gpus {}".format(available_gpus))

    available_cpus = os.getenv('HOTSPUR_THREADS', 2)
    print("Using {} threads".format(available_cpus))


setup_from_environment()
