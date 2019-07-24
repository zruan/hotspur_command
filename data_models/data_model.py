import re
import copy
from hotspur_utils import couchdb_utils

class DataModel():

	def __init__(self, base_name):
		self._id = type(self)._get_id(base_name)
		self.type = type(self)._get_type()
		self.ignored_keys = []

		self.time = None
		self.base_name = base_name

	def __setitem__(self, key, item):
		self.__dict__[key] = item

	def __getitem__(self, key):
		return self.__dict__[key]

	def push(self, db):
		# deepcopy fails as couchdb database doesn't like to be copied
		doc = copy.copy(self.__dict__)
		for key in self.ignored_keys:
			del doc[key]
		del doc['ignored_keys']
		couchdb_utils.push_doc(doc, db)

	def fetch(self, db):
		remote = couchdb_utils.fetch_doc(self._id, db)
		if remote is not None:
			self.__dict__.update(remote)
			return True
		else:
			return False

	@classmethod
	def fetch_all(cls, db):
		doc_type = cls._get_type()
		all_docs = couchdb_utils.fetch_docs_of_type(doc_type, db)
		models = []
		for doc in all_docs:
			model = cls(None)
			model.__dict__.update(doc)
			models.append(model)
		return models

	@classmethod
	def _get_id(cls, base_name):
		class_tag = re.findall('[A-Z][^A-Z]*', cls.__name__)
		class_tag = '_'.join(class_tag)
		class_tag = class_tag.lower()
		if base_name == None:
			id = class_tag
		else:
			id = '{}_{}'.format(base_name, class_tag)
		return id
	
	@classmethod
	def _get_type(cls):
		return cls._get_id(None)
