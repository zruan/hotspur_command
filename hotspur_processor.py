import time

from hotspur_utils import couchdb_utils

from processors import SessionProcessor, FramesFileProcessor, Motioncor2Processor, CtffindProcessor
from hotspur_config import get_config


def start_processing(args):

    if args.dirs is not None:
        search_globs = args.dirs
    else:
        search_globs = get_config().search_globs

    session_processor = SessionProcessor()

    while True:

        for session in session_processor.find_sessions(search_globs):
            FramesFileProcessor.for_session(session).run()
            Motioncor2Processor.for_session(session).run()
            CtffindProcessor.for_session(session).run()
            continue

        time.sleep(5)
