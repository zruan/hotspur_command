import couchdb
from couchdb.design import ViewDefinition

import hotspur_setup

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
		doc[session_name] = session.hash
		push_doc(session_list_doc_name, db)
		print('Added {} to session list.'.format(session.name))
		return True
	except Exception as e:
		print(e)
		raise e

def update_project_list(session):
	try:
		db = fetch_db(admin_db_name)
		doc = fetch_doc(project_list_doc_name, db)
		doc[project_name] = session.project_hash
		push_doc(doc, db)
		print('Added {} to project list.'.format(session.project_name))
		return True
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
	try:
		db[doc._id] = doc
	except:
		remote = db[doc._id]
		remote.update(doc)
		db[doc._id] = remote

def fetch_docs_of_type(doc_type, db):
		map_func = docs_of_type_view_template.substitute(doc_type=doc_type)
		map_func = "".join(map_func.split())
		view = ViewDefinition('hotspur', doc_type, map_func)
		view.sync(db)
		results = view(db)
		return [row.value for row in results.rows]
