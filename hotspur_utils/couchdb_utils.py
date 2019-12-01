import couchdb
from couchdb.design import ViewDefinition
from string import Template
import sys

from hotspur_config import get_config
from hotspur_utils.logging_utils import get_logger_for_module


LOG = get_logger_for_module(__name__)

couchdb_server = couchdb.Server(get_config().couchdb_url)

docs_of_type_view_template = Template(
'''function(doc) {
    if (doc.type && doc.type === "${doc_type}") {
        emit(doc.time, doc)
    }
}'''
)


def fetch_db(db_name):
    if not db_name in couchdb_server:
        LOG.debug(f'Database {db_name} not found')
        LOG.info(f'Creating database {db_name}')
        couchdb_server.create(db_name)
    return couchdb_server[db_name]


def fetch_doc(doc_id, db):

    if doc_id in db:
        LOG.debug(f'Fetching {doc_id} from database {db.name}')
        return db[doc_id]
    else:
        LOG.debug(f'Did not find doc {doc_id} in database {db.name}')
        None


def push_doc(doc, db):
    doc_id = doc['_id']
    if doc_id in db:
        LOG.debug(f'Doc {doc_id} is already present in database {db.name}')
        LOG.debug(f'Updating doc {doc_id} from database {db.name}')
        remote = db[doc_id]
        if '_rev' in doc: del doc['_rev']
        remote.update(doc)
        doc = remote
    LOG.debug(f'Pushing doc {doc_id} to database {db.name}')
    db[doc_id] = doc


def fetch_docs_of_type(doc_type, db):
    LOG.debug(f'Fetching all docs of type {doc_type} from database {db.name}')
    map_func = docs_of_type_view_template.substitute(doc_type=doc_type)
    map_func = "".join(map_func.split())
    view = ViewDefinition('hotspur', doc_type, map_func)
    view.sync(db)
    results = view(db)
    return [row.value for row in results.rows]
