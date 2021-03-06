import logging
from logging.handlers import RotatingFileHandler
import sys
from utils.config import get_config
import tqdm

class TqdmHandler(logging.StreamHandler):
    def __init__(self,status_bar):
        
        logging.StreamHandler.__init__(self)
        self.status_bar = status_bar


    def emit(self, record):
        msg = self.format(record)
        self.status_bar.write(msg)


status_bar = tqdm.tqdm(total=0, position=1, bar_format='{desc}')


full_formatter = logging.Formatter('\n%(levelname)s - %(asctime)s - %(name)s - %(message)s')
short_formatter = logging.Formatter('\n%(levelname)s - %(asctime)s - %(name)s - %(message)s')

sysout_handler = TqdmHandler(status_bar)
sysout_handler.setFormatter(short_formatter)                                                                                        
sysout_handler.setLevel(logging.INFO)

file_handler = RotatingFileHandler(
    get_config().logfile,
    maxBytes=2*1000*1000, # 2MB
    backupCount=5
)
file_handler.setFormatter(full_formatter)
file_handler.setLevel(logging.INFO)

def get_logger_for_module(module_name):
    global sysout_handler
    global file_handler

    logger = logging.getLogger(module_name)                                                                                   
    logger.setLevel(logging.INFO)                                                                                         
    logger.addHandler(sysout_handler)
    logger.addHandler(file_handler)

    return logger

def get_status_bar():
    return status_bar