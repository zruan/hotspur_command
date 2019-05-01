base_path = "/pncc/storage/1/processing/hotspur"
search_glob = [
	'/pncc/storage/1/rawdata/pncc-testing/hotspur-tests/*/*/*/frames/',
	'/pncc/storage/1/rawdata/pncc/*/*/*/frames/',
	'/pncc/storage/1/rawdata/pncc/*/*/*/',
	'/pncc/storage/1/rawdata/pncc-testing/SEM_scripts/test_data_2/'
]

couchdb_address = "http://pncc:cryoem@localhost:5984/"
hash_salt = "feilivinglab-17"

available_gpus = [0, 1, 2, 3]
available_cpus = 12