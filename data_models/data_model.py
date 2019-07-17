import re
import copy
from string import Template
from couchdb.design import ViewDefinition

map_func_template = Template(
'''function(doc) {
	if (doc.type && doc.type === "${doc_type}") {
		emit(doc.time, doc)
	}
}'''
)

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
		doc = copy.deepcopy(self.__dict__)
		for key in keys_to_ignore:
			del doc[key]
		db[doc._id] = doc

	def fetch(self, db):
		try:
			remote_doc = db.get(self._id)
			local_doc = self.__dict__
			local_doc.update(doc)
			self.__dict__ = local_doc
			return True
		except:
			return False

	@classmethod
	def fetch_all(cls, db):
		doc_type = cls._generate_type()
		map_func = map_func_template.substitute(doc_type=doc_type)
		map_func = "".join(map_func.split())
		view = ViewDefinition('hotspur', doc_type, map_func)
		view.sync(db)
		results = view(db)
		docs = [row.value for row in results.rows]
		return docs

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
		return cls._generate_id(None)
