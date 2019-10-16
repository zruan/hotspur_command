import couchdb
from couchdb.design import ViewDefinition
from string import Template
import sys

from hotspur_config import get_config
from hotspur_utils import hash_utils
from data_models import SessionData

couchdb_server = couchdb.Server(get_config().couchdb_url)

docs_of_type_view_template = Template(
'''function(doc) {
    if (doc.type && doc.type === "${doc_type}") {
        emit(doc.time, doc)
    }
}'''
)


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
        if '_rev' in doc.keys():
            del doc['_rev']
        remote.update(doc)
        db[doc_id] = remote


def fetch_docs_of_type(doc_type, db):
        map_func = docs_of_type_view_template.substitute(doc_type=doc_type)
        map_func = "".join(map_func.split())
        view = ViewDefinition('hotspur', doc_type, map_func)
        view.sync(db)
        results = view(db)
        return [row.value for row in results.rows]
