# directory hotspur uses for all its functionality
base_path = "/pncc/storage/1/processing/hotspur"
# path for projects and their sessions, using hashed names for anonymity
projects_hashes_path = base_path + "/projects/hashed"
# path for symlinks to sessions, with plaintext names. For admins to find things
projects_links_path = base_path + "/projects/links"

search_glob = [
	# '/pncc/storage/1/rawdata/pncc-testing/hotspur-tests/*/*/*/frames/',
	'/pncc/storage/1/rawdata/pncc-testing/hotspur-tests/50633/20190429-asic-sma/screening-4/frames/',
	'/goliath/rawdata/MMC/Confometrx/190618/0426-2_2/frames',
	'/pncc/storage/1/rawdata/pncc/*/*/*/frames/',
	'/pncc/storage/1/rawdata/pncc/*/*/*/screen/',
	# '/pncc/storage/1/rawdata/pncc/*/*/*/',
	# '/pncc/storage/1/rawdata/pncc-testing/SEM_scripts/test_data_2/'
]

couchdb_address = "http://pncc:cryoem@localhost:5984/"
hash_salt = "feilivinglab-17"

available_gpus = [0, 1, 2, 3]
available_cpus = 12