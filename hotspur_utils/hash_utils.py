import hashlib
import hotspur_setup

def get_hash(string_to_hash):
	string_to_hash = string_to_hash.encode('utf-8')
	m = hashlib.md5()
	m.update(string_to_hash)
	m.update(hotspur_setup.hash_salt.encode('utf-8'))
	return 'h' + m.hexdigest()