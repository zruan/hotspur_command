#!/eppec/storage/sw/cky-tools/site/bin/python
from multiprocessing import Process
import sys
import glob
import os
from string import Template
import subprocess
import time
import argparse
import string
import getpass
import pyfs
import stat
import imaging
import numpy as np



def file_age_in_seconds(pathname):
    return time.time() - os.stat(pathname)[stat.ST_MTIME]

class PreviewProcessor(Process):
    def __init__(self, process_id, watch_glob, config, min_age=5,sleep=5,work_dir=None, zoom = 0.25):
        Process.__init__(self)
        self.process_id = process_id
        self.watch_glob = watch_glob
        self.config = config
        self.min_age = min_age
        self.sleep = sleep
        self.zoom = zoom
        if work_dir is None:
            self.work_dir = self.config["scratch_dir"]
        else:
            self.work_dir = work_dir

    def create_preview(self, filename):
        image = imaging.load(filename)[0]    
        image = imaging.filters.norm(image, 0.01, 0.01, 0, 255)
        image = imaging.filters.zoom(image, self.zoom)
        picks_path = pyfs.rext(filename) + '.preview.png'
        print(' saving png:', picks_path)
        imaging.save(image, picks_path)

    def run(self):
        os.chdir(self.work_dir)
        idle = 0
        while True:

            file_list = glob.glob(self.watch_glob)
            wait = True
            for filename in file_list:
                lock_filename = self.config["lock_dir"] + filename + "." + self.process_id + ".lck"
                done_filename = self.config["lock_dir"] + filename + "." + self.process_id + ".done"
                if os.path.isfile(lock_filename) or os.path.isfile(done_filename):
                    continue
                if file_age_in_seconds(filename) < self.min_age:
                    continue
                wait = False
                print("Processing %s on %s" % (self.process_id,filename))
                start = time.time()
                with open(lock_filename, 'a'):
                    os.utime(lock_filename, None)

                self.create_preview(filename)
                with open(done_filename, 'a'):
                    os.utime(done_filename, None)

                os.remove(lock_filename)
                end = time.time()
                duration = end-start
                print("Performed %s on %s in %.2f seconds" % (self.process_id,filename, duration) )
            if wait:
                idle += self.sleep 
                if idle > 3600:
                    print("Not processed anything for 60 minutes. %s Exiting." % (self.process_id))
                    break
                time.sleep(self.sleep)
            wait = True

class CommandProcessor(Process):
    def __init__(self, process_id, process_command, watch_glob, config, min_age=1,sleep=5,work_dir=None, ensure_dirs=[], done_lambda=None):
        Process.__init__(self)
        self.process_id = process_id
        self.process_command = process_command
        self.watch_glob = watch_glob
        self.config = config
        self.min_age = min_age
        self.sleep = sleep
        self.ensure_dirs = ensure_dirs
        self.done_lambda = done_lambda
        if work_dir is None:
            self.work_dir = self.config["scratch_dir"]
        else:
            self.work_dir = work_dir


    def run(self):
        os.chdir(self.work_dir)
        idle = 0
        while True:
            if self.done_lambda:
                os.chdir(self.config["lock_dir"])
            file_list = glob.glob(self.watch_glob)
            wait = True
            for filename in file_list:
                if self.done_lambda:
                    os.chdir(self.work_dir)
                    filename = self.done_lambda(filename)
                replace_dict = config.copy()
                replace_dict.update({ "filename" : filename,
                                 "filename_noex" : pyfs.rext(filename, full=True),
                                 "filename_base" : os.path.basename(filename),
                                 "filename_directory" : os.path.dirname(filename),
                                 "filename_base_noext" : pyfs.rext(os.path.basename(filename),full=True),
                               })


                lock_filename = self.config["lock_dir"] + filename + "." + self.process_id + ".lck"
                done_filename = self.config["lock_dir"] + filename + "." + self.process_id + ".done"
                if os.path.isfile(lock_filename) or os.path.isfile(done_filename):
                    continue
                if file_age_in_seconds(filename) < self.min_age:
                    continue
                wait = False
                print("Processing %s on %s" % (self.process_id,filename))
                start = time.time()
                for ensure_dir in self.ensure_dirs:
                    ensure_dir_sub = string.Template(ensure_dir).substitute(replace_dict)
                    if not os.path.exists(ensure_dir_sub):
                        os.makedirs(ensure_dir_sub)
                with open(lock_filename, 'a'):
                    os.utime(lock_filename, None)

                command = Template(self.process_command).substitute(replace_dict)
                print(command)
                res = subprocess.run(command,shell=True)

                with open(done_filename, 'a'):
                    os.utime(done_filename, None)

                os.remove(lock_filename)
                end = time.time()
                duration = end-start
                print("Performed %s on %s in %.2f seconds" % (self.process_id,filename, duration) )
            if wait:
                idle += self.sleep 
                if idle > 3600:
                    print("Not processed anything for 60 minutes. %s Exiting." % (self.process_id))
                    break
                time.sleep(self.sleep)
            wait = True

def arguments():

    def floatlist(string):
        return list(map(float, string.split(',')))

    parser = argparse.ArgumentParser(
        description='Runs data processing live for incoming data')
    
    parser.add_argument('--init', default=False, action='store_true',  help='Initiates configuration file. Should be adjusted before starting')
    parser.add_argument('--config', help='Configuration file to use', default="config.py")
    
    return parser.parse_args()



if __name__ == '__main__':
    
    args = arguments()
    print(args)

    if args.init:
        with open(os.path.join(os.path.dirname(__file__),"collection_processor/config.py"), 'r') as config_file:
           template = string.Template(config_file.read())
        config_processed = template.substitute(curr_dir=os.getcwd(),
                               user=getpass.getuser(),
                               curr_dir_base=os.path.basename(os.path.normpath(os.getcwd())))
        with open(args.config, 'w') as config_file:
           config_file.write(config_processed)



        sys.exit()
    with open(args.config, 'r') as config_file:
        exec(config_file.read(), globals())


    if not os.path.exists(config["scratch_dir"]):
        os.makedirs(config["scratch_dir"])
    if not os.path.exists(config["lock_dir"]):
        os.makedirs(config["lock_dir"])

    for process in processes:
        process.start()
    for process in processes:
        process.join()
