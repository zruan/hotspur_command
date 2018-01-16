from multiprocessing import Process
import pyfs
import os
import glob
from time import sleep
import time
from random import randint
import stat
import string
import traceback

def file_age_in_seconds(pathname):
    return time.time() - os.stat(pathname)[stat.ST_MTIME]

class CollectionProcessor(Process):

    def __init__(
            self,
            process_id,
            config,
            watch_glob=None,
            min_age=1,
            sleep=5,
            work_dir=None,
            ensure_dirs=[],
            depends=None,
            done_lambda=lambda stackname, process_id, config: config[
                "lock_dir"] + stackname + "." + process_id + ".done",
            lock_lambda=lambda stackname, process_id, config: config[
                "lock_dir"] + stackname + "." + process_id + ".lck",
            error_lambda=lambda stackname, process_id, config: config[
                "lock_dir"] + stackname + "." + process_id + ".err",
    ):
        Process.__init__(self)
        self.process_id = process_id
        if watch_glob is None:
            if depends is None:
                raise ValueError(
                    "Need to specify etiher watch_glob or dependency")
            else:
                self.watch_glob = done_lambda(
                    pyfs.rext(config["glob"]), depends, config)
        else:
            self.watch_glob = watch_glob
        self.config = config
        self.min_age = min_age
        self.sleep = sleep
        self.depends = depends
        self.ensure_dirs = ensure_dirs
        self.done_lambda = done_lambda
        self.lock_lambda = lock_lambda
        self.error_lambda = error_lambda
        if work_dir is None:
            self.work_dir = self.config["scratch_dir"]
        else:
            self.work_dir = work_dir

    def run(self):
        os.chdir(self.work_dir)
        idle = 0
        while True:
            try:
                file_list = glob.glob(self.watch_glob)
                wait = True
                sleep(randint(100,1000)*0.001)
                for filename in file_list:
                    replace_dict = self.config.copy()
                    if self.depends:
                        filename = filename[len(self.config["lock_dir"]):-len(".done")]
                    stackname = pyfs.rext(filename, full=False)
                    replace_dict.update({
                        "filename": filename,
                        "filename_noex": pyfs.rext(
                            filename, full=False),
                        "filename_base": os.path.basename(filename),
                        "filename_directory": os.path.dirname(filename),
                        "filename_base_noext": pyfs.rext(
                            os.path.basename(filename), full=False),
                        "stackname": stackname
                    })

                    lock_filename = self.lock_lambda(stackname,
                                                     self.process_id, self.config)
                    done_filename = self.done_lambda(stackname,
                                                     self.process_id, self.config)
                    error_filename = self.error_lambda(stackname,
                                                     self.process_id, self.config)
                    if self.min_age > 0 and file_age_in_seconds(
                            filename) < self.min_age:
                        continue
                    if os.path.isfile(lock_filename) or os.path.isfile(
                            done_filename):
                        continue
                    try:
                        for ensure_dir in self.ensure_dirs:
                            ensure_dir_sub = string.Template(
                                ensure_dir).substitute(replace_dict)
                            if not os.path.exists(ensure_dir_sub):
                                try:
                                    os.makedirs(ensure_dir_sub)
                                except IOError as e:
                                    print("Could not create directory %s" %
                                          (ensure_dir))
                        with open(lock_filename, 'a'):
                            os.utime(lock_filename, None)
                        wait = False
                        print("Processing %s on %s" %
                              (self.process_id, filename))
                        start = time.time()

                        try:
                            self.run_loop(self.config, replace_dict)
                        except KeyboardInterrupt:
                            raise KeyboardInterrupt
                        except:
                            with open(error_filename, 'w') as fp:
                                traceback.print_exc(file=fp)


                        with open(done_filename, 'a'):
                            os.utime(done_filename, None)

                        os.remove(lock_filename)
                        end = time.time()
                        duration = end - start
                        print("Performed %s on %s in %.2f seconds" %
                              (self.process_id, filename, duration))
                    except KeyboardInterrupt:
                        print("%s received Ctr-C. Cleaning up:" %
                              (self.process_id))
                        os.remove(lock_filename)
                        raise KeyboardInterrupt
                if wait:
                    idle += self.sleep
                    if idle > 36000:
                        print(
                            "Not processed anything for 600 minutes. %s Exiting."
                            % (self.process_id))
                        break
                    start = time.time()
                    time.sleep(self.sleep)
                    end = time.time()
                    duration = end - start
                wait = True
            except KeyboardInterrupt:
                print("%s received Ctrl-C" % (self.process_id))
                return
