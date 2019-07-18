import couchdb

import hotspur_setup

def update_session_list(session):
	try:
		project_db = get_db(session.project_hash)
		session_list_doc = get_doc(session_list_doc_name)
		session_list_doc[session_name] = session.hash
		project_db[session_list_doc_name] = doc
		print('Added {} to session list.'.format(session.name))
		return True
	except Exception as e:
		print(e)
		raise e


def update_project_list(session):
	try:
		doc = get_doc(admin_db, project_list_doc_name)
		doc[project_name] = session.project_hash
		admin_db[project_list_doc_name] = doc
		print('Added {} to project list.'.format(session.project_name))
		return True
	except Exception as e:
		print(e)
		raise e

def get_db(db_name):
	try:
		db = couchdb_server.create(db_name)
	except couchdb.http.PreconditionFailed:
		db = couchdb_server[db_name]
	return db

def get_doc(db, doc_name):
	try:
		doc = db[doc_name]
	except:
		doc = {'_id': doc_name}
		db[doc_name] = doc
	return doc

couchdb_server = couchdb.Server(hotspur_setup.couchdb_address)

admin_db_name = 'projects_overview'
project_list_doc_name = 'projects_overview'
session_list_doc_name = 'sessions_overview'

admin_db = get_db(admin_db_name)