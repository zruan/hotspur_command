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
