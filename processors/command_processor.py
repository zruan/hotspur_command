import string
from string import Template
import subprocess
from processors import CollectionProcessor

class CommandProcessor(CollectionProcessor):

    def __init__(self, process_id, process_command, config, **kwargs):
        CollectionProcessor.__init__(self, process_id, config, **kwargs)
        self.process_command = process_command

    def run_loop(self, config, replace_dict):
        command = Template(self.process_command).substitute(replace_dict)
        res = subprocess.run(command, shell=True)