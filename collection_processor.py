import sys
import glob
import os
import argparse
import pyfs
import time

import couchdb

from processors import SessionProcessor, FramesFileProcessor, Motioncor2Processor, CtffindProcessor
import hotspur_setup


def arguments():
    parser = argparse.ArgumentParser(
        description='Runs data processing live for incoming data'
    )
    parser.add_argument(
        '--target-dir',
        dest='target_dir',
        help='A directory you want to process. This is for when you only want to process one session.'
    )
    parser.add_argument(
        '--reset-all',
        dest='reset_all',
        help="Remove all processing for every session.",
        action='store_true'
    )
    parser.add_argument(
        '--reset-dir',
        dest='reset_dir',
        help="Reset all processing done on given data directory."
    )
    return parser.parse_args()

def reset_session(session):
    server = couchdb.Server(hotspur_setup.couchdb_address)
    db = SessionProcessor.session_databases[session]
    print('Deleting database "{}"...'.format(db.name))
    try:
        server.delete(db.name)
        print('Database deleted.')
    except:
        print('Database could not be deleted. Skipping...')

def reset_all():
    server = couchdb.Server(hotspur_setup.couchdb_address)
    db = server['hashlinks']
    for doc_summary in db.view('_all_docs'):
        doc = db[doc_summary.id]
        db_name = doc['db_name']
        print('Deleting database "{}"...'.format(db_name))
        try:
            server.delete(doc['db_name'])
            print('Database deleted.')
        except:
            print('Database could not be deleted. Skipping...')
    server.delete('hashlinks')

def start_processing():
    args = arguments()

    if args.reset_all:
        reset_all()
        exit()

    if args.reset_dir is not None:
        session = SessionProcessor.create_new_session(args.reset_dir)
        reset_session(session)
        exit()
    
    if args.target_dir is not None:
        search_glob = args.target_dir
    else:
        search_glob = hotspur_setup.search_glob

    frames_file_processor = FramesFileProcessor()
    motioncor2_processor = Motioncor2Processor()
    ctffind_processor = CtffindProcessor()

    for session in SessionProcessor.find_sessions(search_glob):
        frames_file_processor.update_from_couchdb(session)

    while True:
        for session in SessionProcessor.find_sessions(search_glob):
            # frames_file_processor.run(session)
            motioncor2_processor.run(session)
            ctffind_processor.run(session)
        time.sleep(5)

if __name__ == '__main__':
    start_processing()
