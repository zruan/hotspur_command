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

couchdb_address = "http://pncc:cryoem@localhost:5984/"
hash_salt = "feilivinglab-17"

available_gpus = [0, 1, 2, 3]
available_cpus = 12

# Maximum age of directory for valid session, in days.
# If mod time of directory is older, it will be skipped.
# Run `touch /path/to/dir` on the command line to refresh the mod time.
session_max_age = 7