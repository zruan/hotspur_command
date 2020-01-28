import time
import random
import tqdm
import time

from utils.logging import get_logger_for_module, get_status_bar
from utils.resources import ResourceManager
from utils.config import get_config

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

session_tracking_interval = 300

LOG = get_logger_for_module(__name__)

STATUS_BAR = get_status_bar()


def run(args):

    search_patterns = get_config().search_patterns
    tot_cpus = get_config().threads

    session_processor = SessionProcessor()
    project_processor = ProjectProcessor()

    last_session_tracking = None
    last_main_loop = None

    while True:
        if last_main_loop is not None:
            main_loop_time = time.time() - last_main_loop
        else:
            main_loop_time = time.time()
        last_main_loop = time.time()
        STATUS_BAR.set_description_str(f'CPU: {ResourceManager.available_cpus}/{tot_cpus} GPU: {sum(map(lambda x: not x[1].locked(),ResourceManager.gpu_locks))}/{len(ResourceManager.gpu_locks)} Sessions: {len(session_processor.sessions)} Mainloop time: {main_loop_time}')
        
        if last_session_tracking is None or time.time() - last_session_tracking >= session_tracking_interval:
            session_processor.find_sessions(search_patterns)
            last_session_tracking = time.time()

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
