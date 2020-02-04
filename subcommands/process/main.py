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
import signal
import sys


def signal_handler(sig, frame):
    global stop_hotspur
    LOG.exception('You pressed Ctrl+C! Exiting Hotspur gracefully. You will see errors because programs are being canceled.')
    stop_hotspur = True

signal.signal(signal.SIGINT, signal_handler)


stop_hotspur=False

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
    t = time.time()

    timer = {"SES" : 0, "PRO": 0, "NAV": 0, "MON": 0, "FRA": 0, "MC": 0, "CTF": 0, "DOG": 0}

    while True:
        if last_main_loop is not None:
            main_loop_time = time.time() - last_main_loop
        else:
            main_loop_time = time.time()
        last_main_loop = time.time()
        STATUS_BAR.set_description_str(f'CPU: {ResourceManager.available_cpus}/{tot_cpus} GPU: {sum(map(lambda x: not x[1].locked(),ResourceManager.gpu_locks))}/{len(ResourceManager.gpu_locks)} Sessions: {len(session_processor.sessions)} Mainloop time: {main_loop_time} {timer}')
        
        if last_session_tracking is None or time.time() - last_session_tracking >= session_tracking_interval:
            session_processor.find_sessions(search_patterns)
            last_session_tracking = time.time()
        timer["SES"] += time.time() - t
        t = time.time()
        random.shuffle(session_processor.sessions)

        for session in session_processor.sessions:
            project_processor.update_project(session)
            timer["PRO"] += time.time() - t
            t = time.time()
            NavigatorProcessor.for_session(session).run()
            timer["NAV"] += time.time() - t
            t = time.time()
            MontageProcessor.for_session(session).run()
            timer["MON"] += time.time() - t
            t = time.time()
            FramesFileProcessor.for_session(session).run()
            timer["FRA"] += time.time() - t
            t = time.time()
            Motioncor2Processor.for_session(session).run()
            timer["MC"] += time.time() - t
            t = time.time()
            CtffindProcessor.for_session(session).run()
            timer["CTF"] += time.time() - t
            t = time.time()
            DogpickerProcessor.for_session(session).run()
            timer["DOG"] += time.time() - t
            t = time.time()

        time.sleep(0.1)
        if (stop_hotspur):
            break
