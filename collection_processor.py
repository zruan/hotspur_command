import sys
import glob
import os
import argparse
import pyfs
import time

from hotspur_utils import couchdb_utils

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
        help="Reset all projects",
        action='store_true'
    )
    parser.add_argument(
        '--reset-project',
        dest='reset_project',
        help="Reset all sessions for project with given name"
    )
    parser.add_argument(
        '--reset-session',
        dest='reset_session',
        help="Reset all processing done for given frames directory."
    )
    return parser.parse_args()

def start_processing():
    args = arguments()


    if args.reset_all:
        couchdb_utils.reset_all()
        exit()
    
    if args.reset_project is not None:
        couchdb_utils.reset_project(args.reset_project)
        exit()

    session_processor = SessionProcessor()

    if args.reset_session is not None:
        session = session_processor.create_new_session(args.reset_session)
        couchdb_utils.reset_session(session)
        exit()

    if args.target_dir is not None:
        search_globs = [args.target_dir]
    else:
        search_globs = hotspur_setup.search_globs

    while True:
        for session in session_processor.find_sessions(search_globs):
            FramesFileProcessor.for_session(session).run()
            # Motioncor2Processor.for_session(session).run()
            # CtffindProcessor.for_session(session).run()
        time.sleep(5)

if __name__ == '__main__':
    start_processing()
