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

def format_string(counter):
    string = ""
    for k,v in counter.items():
        string += k + ": "
        string += str(v["T"]) +"/"
        string += str(v["Q"]) +"/"
        string += str(v["F"]) +"/"
        string += str(v["X"]) +" "
    return string


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
    counter = {
        "FRA": { "T":0, "Q":0,"F":0,"X":0},
        "MO": { "T":0, "Q":0,"F":0,"X":0},
        "DOG": { "T":0, "Q":0,"F":0,"X":0},
    }


    while True:
        if last_main_loop is not None:
            main_loop_time = time.time() - last_main_loop
        else:
            main_loop_time = time.time()
        last_main_loop = time.time()
        STATUS_BAR.set_description_str(f'CPU: {ResourceManager.available_cpus}/{tot_cpus} GPU: {sum(map(lambda x: not x[1].locked(),ResourceManager.gpu_locks))}/{len(ResourceManager.gpu_locks)} Sessions: {len(session_processor.sessions)} Mainloop time: {main_loop_time:.3f} {format_string(counter)}')
        
        if last_session_tracking is None or time.time() - last_session_tracking >= session_tracking_interval:
            session_processor.find_sessions(search_patterns)
            last_session_tracking = time.time()
        random.shuffle(session_processor.sessions)
        counter = {
        "FRA": { "T":0, "Q":0,"F":0,"X":0},
        "MO": { "T":0, "Q":0,"F":0,"X":0},
        "DOG": { "T":0, "Q":0,"F":0,"X":0},
        }
        for session in session_processor.sessions:
            project_processor.update_project(session)
            NavigatorProcessor.for_session(session).run()
            MontageProcessor.for_session(session).run()
            FramesFileProcessor.for_session(session).run()
            counter["FRA"]["T"] += len(FramesFileProcessor.for_session(session).tracked)
            counter["FRA"]["Q"] += len(FramesFileProcessor.for_session(session).queued)
            counter["FRA"]["F"] += len(FramesFileProcessor.for_session(session).finished)
            counter["FRA"]["X"] += len(FramesFileProcessor.for_session(session).failed)
            Motioncor2Processor.for_session(session).run()
            counter["MO"]["T"] += len(Motioncor2Processor.for_session(session).tracked)
            counter["MO"]["Q"] += len(Motioncor2Processor.for_session(session).queued)
            counter["MO"]["F"] += len(Motioncor2Processor.for_session(session).finished)
            counter["MO"]["X"] += len(Motioncor2Processor.for_session(session).failed)
            CtffindProcessor.for_session(session).run()
            DogpickerProcessor.for_session(session).run()
            counter["DOG"]["T"] += len(DogpickerProcessor.for_session(session).tracked)
            counter["DOG"]["Q"] += len(DogpickerProcessor.for_session(session).queued)
            counter["DOG"]["F"] += len(DogpickerProcessor.for_session(session).finished)
            counter["DOG"]["X"] += len(DogpickerProcessor.for_session(session).failed)
            
        time.sleep(0.1)
        if (stop_hotspur):
            break
