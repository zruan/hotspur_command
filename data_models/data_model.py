import couchdb
import re


class DataModel():

	def __init__(self, base_name):
		self._id = type(self)._generate_id(base_name)

	def save_to_couchdb(self, db):
		db.save(self.__dict__)

	@classmethod
	def read_from_couchdb_by_name(cls, db, base_name=''):
		id = cls._generate_id(base_name)
		data_model = cls(base_name)
		data_model.__dict__ = db.load(id)
		return data_model

	@classmethod
	def _generate_id(cls, base_name):
		class_tag = re.findall('[A-Z][^A-Z]*', cls.__name__)
		class_tag = '_'.join(class_tag)
		class_tag = class_tag.lower()
		return base_name + '_' + cls.__name__.lower()
