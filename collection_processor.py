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
        '--target-dirs',
        dest='target_dirs',
        help='Process all directories matching given directories',
        nargs='+'
    )
    parser.add_argument(
        '--reset-all',
        dest='reset_all',
        help="Reset all projects",
        action='store_true'
    )
    parser.add_argument(
        '--reset-project',
        dest='project_to_reset',
        help="Reset all sessions for project with given name"
    )
    parser.add_argument(
        '--reset-dirs',
        dest='dirs_to_reset',
        help="Reset all processing done for given directories",
        nargs='+'
    )
    return parser.parse_args()

def start_processing():
    args = arguments()

    if args.reset_all:
        couchdb_utils.reset_all()
        exit()
    
    if args.project_to_reset is not None:
        couchdb_utils.reset_project(args.project_to_reset)
        exit()

    session_processor = SessionProcessor()

    if args.dirs_to_reset is not None:
        for session in session_processor.find_sessions(args.dirs_to_reset):
            try:
                couchdb_utils.reset_session(session)
            except:
                continue
        exit()

    if args.target_dirs is not None:
        search_globs = args.target_dirs
    else:
        search_globs = hotspur_setup.search_globs

    while True:
        for session in session_processor.find_sessions(search_globs):
            FramesFileProcessor.for_session(session).run()
            Motioncor2Processor.for_session(session).run()
            # CtffindProcessor.for_session(session).run()
            continue
        time.sleep(5)

if __name__ == '__main__':
    start_processing()
