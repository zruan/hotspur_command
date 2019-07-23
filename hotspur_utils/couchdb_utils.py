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
		doc = fetch_doc(session_list_doc_name, db, True)
		try:
			name = doc[session.name]
			print('Session {} is already in session list for project {}'.format(
			    session.name, session.project_name))
		except:
			doc[session.name] = session.hash
			push_doc(doc, db)
			print('Added session {} to session list for project {}'.format(
			    session.name, session.project_name))
	except Exception as e:
		print('Failed to add session {} to session list for project {}'.format(
		    session.name, session.project_name))
		print(e)
		raise e


def update_project_list(session):
	try:
		db = fetch_db(admin_db_name)
		doc = fetch_doc(project_list_doc_name, db, True)
		try:
			name = doc[session.project_name]
			print('Project {} is already in project list'.format(session.project_name))
		except:
			doc[session.project_name] = session.project_hash
			push_doc(doc, db)
			print('Added project {} to project list'.format(session.project_name))
	except Exception as e:
		print('Failed add project {} to project list'.format(session.project_name))
		print(e)
		raise e


def fetch_db(db_name):
	try:
		db = couchdb_server.create(db_name)
	except couchdb.http.PreconditionFailed:
		db = couchdb_server[db_name]
	return db


def fetch_doc(doc_id, db, default=False):
	try:
		return db[doc_id]
	except:
		if default:
			doc = {'_id': doc_id}
			db[doc_id] = doc
			return doc
		else:
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
		if doc is None:
			raise Exception()
	except:
		print('Failed to retrieve list of projects')
		return

	for key in doc.keys():
		if key in ['_id', '_rev']:
			continue
		project_name = key
		try:
			reset_project(project_name)
		except:
			continue


def reset_project(project_name):
	project_hash = hash_utils.get_hash(project_name)
	try:
		db = fetch_db(project_hash)
		doc = fetch_doc(session_list_doc_name, db)
		if doc is None:
			raise Exception()
	except:
		print('Failed to retrieve list of sessions')
		return

	all_sessions_reset = True
	for key, val in doc.items():
		if key in ['_id', '_rev']:
			continue

		session_name = key
		session_hash = val

		try:
			couchdb_server.delete(session_hash)
			print('Deleted session database {}'.format(session_hash))
		except:
			all_sessions_reset = False
			continue

		try:
			db = fetch_db(project_hash)
			doc = fetch_doc(session_list_doc_name, db)
			del doc[session_name]
			push_doc(doc, db)
			print('Removed {} from session list for project {}'.format(session_name, project_name))
		except Exception as e:
			print('Failed to remove {} from session list for project {}'.format(session_name, project_name))
			print(e)
			raise e

	if not all_sessions_reset:
		print("Not all sessions deleted. Leaving project database")
		return

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

	return

def reset_session(session):
	try:
		couchdb_server.delete(session.hash)
		print('Deleted session database {}'.format(session.hash))
	except Exception as e:
		print('Failed to delete session database {}'.format(session.hash))
		print(e)
		raise e

	try:
		db = fetch_db(session.project_hash)
		doc = fetch_doc(session_list_doc_name, db)
		del doc[session.name]
		push_doc(doc, db)
		print('Removed {} from session list for project {}'.format(session.name, session.project_name))
	except Exception as e:
		print('Failed to remove {} from session list for project {}'.format(session.name, session.project_name))
		print(e)
		raise e
