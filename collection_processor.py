#!/eppec/storage/sw/cky-tools/site/bin/python
from multiprocessing import Process
import sys
import glob
import os
from string import Template
import subprocess
import time



config = {
        "collection_dir" : "${collection_dir}",
        "scratch_dir" : "/tmp/JE_test",
        "archive_dir" : "/tmp/JE_test_archive",
        "lock_dir"    : "/tmp/JE_test" + "/lock/"
        }


class CommandProcessor(Process):
    def __init__(self, process_id, process_command, watch_glob, config, min_age=1,work_dir=None):
        Process.__init__(self)
        self.process_id = process_id
        self.process_command = process_command
        self.watch_glob = watch_glob
        self.config = config
        self.min_age = min_age
        if work_dir is None:
            self.work_dir = self.config["scratch_dir"]
        else:
            self.work_dir = work_dir

    def run(self):
        os.chdir(self.work_dir)

        while True:

            file_list = glob.glob(self.watch_glob)
            wait = True
            for filename in file_list:
                lock_filename = self.config["lock_dir"] + filename + "." + self.process_id + ".lck"
                done_filename = self.config["lock_dir"] + filename + "." + self.process_id + ".done"
                if os.path.isfile(lock_filename) or os.path.isfile(done_filename):
                    continue
                wait = False
                print("Processing %s on %s" % (self.process_id,filename))
                start = time.time()
                with open(lock_filename, 'a'):
                    os.utime(lock_filename, None)

                command = Template(self.process_command).substitute(filename=filename)
                res = subprocess.run(command,shell=True)

                with open(done_filename, 'a'):
                    os.utime(done_filename, None)

                os.remove(lock_filename)
                end = time.time()
                duration = end-start
                print("Performed %s on %s in %.2f seconds" % (self.process_id,filename, duration) )
            if wait:
                time.sleep(5)
            wait = True

if __name__ == "__main__":

    if not os.path.exists(config["scratch_dir"]):
        os.makedirs(config["scratch_dir"])
    if not os.path.exists(config["lock_dir"]):
        os.makedirs(config["lock_dir"])

    Test_processor = CommandProcessor("test_cp", "cp ${filename} ${filename}.cop && sleep 10", "test*.obj", config, work_dir = os.getcwd())
    Test_processor.run()
    Test_processor.join()

