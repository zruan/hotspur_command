import sys
import glob
import os
import argparse
import pyfs
import time

from hotspur_utils import couchdb_utils

from processors import SessionProcessor, FramesFileProcessor, Motioncor2Processor, CtffindProcessor
import hotspur_setup


def start_processing(args):

    # if args.reset_all:
    #     couchdb_utils.reset_all()
    #     exit()
    
    # if args.project_to_reset is not None:
    #     couchdb_utils.reset_project(args.project_to_reset)
    #     exit()


    # if args.dirs_to_reset is not None:
    #     for session in session_processor.find_sessions(args.dirs_to_reset):
    #         try:
    #             couchdb_utils.reset_session(session)
    #         except:
    #             continue
    #     exit()
    
    # if args.reset_found_sessions:
    #     for session in session_processor.find_sessions(hotspur_setup.search_globs):
    #         try:
    #             couchdb_utils.reset_session(session)
    #         except:
    #             continue
    #     exit()
    

    if args.dirs is not None:
        search_globs = args.dirs
    else:
        search_globs = hotspur_setup.search_globs

    while True:

        session_processor = SessionProcessor()

        for session in session_processor.find_sessions(search_globs):
            FramesFileProcessor.for_session(session).run()
            Motioncor2Processor.for_session(session).run()
            CtffindProcessor.for_session(session).run()
            continue

        time.sleep(5)
