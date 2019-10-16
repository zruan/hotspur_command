import hashlib
from hotspur_config import get_config

def get_hash(string_to_hash):
	string_to_hash = string_to_hash.encode('utf-8')
	m = hashlib.md5()
	m.update(string_to_hash)
	m.update(get_config().salt.encode('utf-8'))
	return 'h' + m.hexdigest()