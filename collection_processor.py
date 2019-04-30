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
        '--target_dir',
        metavar='target-dir',
        help='A directory you want to process. This is for when you only want to process one session.'
    )
    parser.add_argument(
        '--reset',
        help="Remove all '.done' files that track processing progress.",
        action='store_true'
    )
    return parser.parse_args()

def reset_processing(session_data):
    print("Removing '.done' files...")
    for file in os.listdir(session_data.processing_directory):
        if file.endswith('.done'):
            file_path = os.path.join(session_data.processing_directory, file)
            os.remove(file_path)
    print("Successfully removed '.done' files.")

    server = couchdb.Server(hotspur_setup.couchdb_address)
    db = SessionProcessor.get_couchdb_database(
        session_data.user,
        session_data.grid,
        session_data.session
    )
    print('Deleting database "{}"...'.format(db.name))
    server.delete(db.name)
    print('Database deleted.')


def start_processing():
    args = arguments()

    # session_data = SessionProcessor.create_new_session(args.target_dir)
    # prepare_directory_structure(session_data)

    # if args.reset:
    #     reset_processing(session_data)
    #     exit()

    session_processor = SessionProcessor()
    frames_file_processor = FramesFileProcessor()
    motioncor2_processor = Motioncor2Processor()
    ctffind_processor = CtffindProcessor()

    while True:
        for session in session_processor.find_sessions(hotspur_setup.search_glob):
            print(session.frames_directory)
            exit()
            frames_file_processor.run(session)
            motioncor2_processor.run(session)
            ctffind_processor.run(session)
        time.sleep(5)
