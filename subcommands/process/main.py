import time
import random

from utils.logging import get_logger_for_module
from utils.resources import ResourceManager

from processors import (
    SessionProcessor,
    ProjectProcessor,
    NavigatorProcessor,
    MontageProcessor,
    FramesFileProcessor,
    Motioncor2Processor,
    CtffindProcessor,
    DogpickerProcessor
)

from utils.config import get_config


LOG = get_logger_for_module(__name__)

def run(args):

    search_patterns = get_config().search_patterns

    session_processor = SessionProcessor()
    project_processor = ProjectProcessor()

    while True:
        LOG.debug('Starting main loop')
        LOG.info(f'Processing {len(session_processor.sessions)} sessions')
        LOG.info(f'Available CPUs: {ResourceManager.available_cpus} ')
        LOG.info(f'Available GPUs: {ResourceManager.gpu_locks} ')
        session_processor.find_sessions(search_patterns)
        random.shuffle(session_processor.sessions)

        for session in session_processor.sessions:
            project_processor.update_project(session)
            NavigatorProcessor.for_session(session).run()
            MontageProcessor.for_session(session).run()
            FramesFileProcessor.for_session(session).run()
            Motioncor2Processor.for_session(session).run()
            CtffindProcessor.for_session(session).run()
            DogpickerProcessor.for_session(session).run()

        time.sleep(1)
