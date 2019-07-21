import couchdb
from couchdb.design import ViewDefinition
from string import Template

import hotspur_setup
from hotspur_utils import hash_utils
from processors import SessionProcessor
from data_models import SessionData

couchdb_server = couchdb.Server(hotspur_setup.couchdb_address)

admin_db_name = 'projects_overview'
project_list_doc_name = 'projects_overview'
session_list_doc_name = 'sessions_overview'

docs_of_type_view_template = Template(
'''function(doc) {
	if (doc.type && doc.type === "${doc_type}") {
		emit(doc.time, doc)
	}
}'''
)

def update_session_list(session):
	try:
		db = fetch_db(session.project_hash)
		doc = fetch_doc(session_list_doc_name, db)
		doc[session.name] = session.hash
		push_doc(doc, db)

	except Exception as e:
		print(e)
		raise e

def update_project_list(session):
	try:
		db = fetch_db(admin_db_name)
		doc = fetch_doc(project_list_doc_name, db)
		doc[session.project_name] = session.project_hash
		push_doc(doc, db)

	except Exception as e:
		print(e)
		raise e

def fetch_db(db_name):
	try:
		db = couchdb_server.create(db_name)
	except couchdb.http.PreconditionFailed:
		db = couchdb_server[db_name]
	return db

def fetch_doc(doc_id, db):
	try:
		return db[doc_id]
	except:
		return None

def push_doc(doc, db):
	doc_id = doc['_id']
	try:
		db[doc_id] = doc
	except:
		remote = db[doc_id]
		remote.update(doc)
		db[doc_id] = remote

def fetch_docs_of_type(doc_type, db):
		map_func = docs_of_type_view_template.substitute(doc_type=doc_type)
		map_func = "".join(map_func.split())
		view = ViewDefinition('hotspur', doc_type, map_func)
		view.sync(db)
		results = view(db)
		return [row.value for row in results.rows]

def reset_all():
	try:
		db = fetch_db(admin_db_name)
		doc = fetch_doc(project_list_doc_name, db)
	except:
		print('Failed to retrieve list of projects')
		return

	for key in doc.keys():
		if key in ['_id', '_rev']:
			continue
		project_name = key
		reset_project(project_name)

def reset_project(project_name):
	project_hash = hash_utils.get_hash(project_name)
	try:
		db = fetch_db(project_hash)
		doc = fetch_doc(session_list_doc_name, db)
	except:
		print('Failed to retrieve list of sessions')
		return

	for key, val in doc:
		if key in ['_id', '_rev']:
			continue
		session_hash = val
		session = SessionData()
		try:
			session.fetch(session_hash)
			print("Fetched session data")
		except:
			print("Failed to fetch session data")
			return
		reset_session(session)

	try:
		couchdb_server.delete(project_hash)
		print("Deleted project database {}".format(project_hash))
	except:
		print("Failed to delete project database {}".format(project_hash))
		return

	try:
		db = fetch_db(admin_db_name)
		doc = fetch_doc(project_list_doc_name, db)
		del doc[project_name]
		push_doc(doc, db)
		print('Removed {} from project list'.format(project_name))
	except:
		print('Failed to remove {} from project list'.format(project_name))
		return

def reset_session(session):
	try:
		couchdb_server.delete(key)
		print('Deleted session database {}'.format(key))
	except:
		print('Failed to delete session database {}'.format(key))
		return

	try:
		db = fetch_db(session.project_hash)
		doc = fetch_doc(session_list_doc_name, db)
		del doc[session.name]
		push_doc(doc, db)
		print('Removed {} from session list for project {}'.format(session.project_name))
	except:
		print('Failed to remove {} from session list for project {}'.format(session.project_name))
		return
