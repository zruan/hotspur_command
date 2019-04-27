import os

base_path = "/pncc/storage/1/processing/hotspur"
config_dir = os.path.join(base_path, "configs")
hashlinks_dir = os.path.join(base_path, "hashlinks")
hash_salt = "feilivinglab-17"
couchdb_address = "http://localhost:5984/"
available_gpus = [0, 1, 2, 3]
available_cpus = 12