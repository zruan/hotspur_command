import re
from string import Template
from couchdb.design import ViewDefinition

map_func_template = Template(
'''function(doc) {
	if (doc.type === "${doc_type}") {
		emit(doc.time, doc.base_name)
	}
}'''
)

class DataModel():

	query = None

	def __init__(self, base_name):
		self._id = type(self)._generate_id(base_name)
		self.type = type(self)._generate_type()
		self.time = None
		self.base_name = base_name

	def save_to_couchdb(self, db):
		db.save(self.__dict__)

	@classmethod
	def read_from_couchdb_by_name(cls, db, base_name=None):
		data_model = cls(base_name)
		data_model.__dict__ = db.get(data_model._id)
		return data_model

	@classmethod
	def _generate_id(cls, base_name):
		class_tag = re.findall('[A-Z][^A-Z]*', cls.__name__)
		class_tag = '_'.join(class_tag)
		class_tag = class_tag.lower()
		if base_name == None:
			id = class_tag
		else:
			id = '{}_{}'.format(base_name, class_tag)
		return id
	
	@classmethod
	def _generate_type(cls):
		return cls._generate_id(None)
	
	@classmethod
	def find_docs_by_time(cls, db):
		doc_type = cls._generate_type()
		map_func = map_func_template.substitute(doc_type=doc_type)
		map_func = "".join(map_func.split())
		view = ViewDefinition('hotspur', doc_type, map_func)
		view.sync(db)
		results = view(db)
		doc_listings = [DataModelSummary(row.value, row.key, row.id) for row in results.rows]
		return doc_listings

class DataModelSummary():

	def __init__(self, base_name, id, time):
		self.base_name = base_name
		self.id = id
		self.time = time

	def __eq__(self, other):
		if self.base_name == other.base_name:
			return True
		else:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)