import logging
from logging.handlers import RotatingFileHandler
import sys
from hotspur_config import get_config


full_formatter = logging.Formatter('\n%(levelname)s - %(asctime)s - %(name)s - %(message)s')
short_formatter = logging.Formatter('\n%(levelname)s - %(name)s - %(message)s')

sysout_handler = logging.StreamHandler(sys.stdout)
sysout_handler.setFormatter(short_formatter)                                                                                        
sysout_handler.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(
    get_config().logfile,
    maxBytes=10000,
    backupCount=5
)
file_handler.setFormatter(full_formatter)
file_handler.setLevel(logging.DEBUG)

def get_logger_for_module(module_name):
    global sysout_handler
    global file_handler

    logger = logging.getLogger(module_name)                                                                                   
    logger.setLevel(logging.DEBUG)                                                                                         
    logger.addHandler(sysout_handler)
    logger.addHandler(file_handler)

    return logger