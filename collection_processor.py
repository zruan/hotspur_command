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
from collection_parser import ParserProcess, MotionCor2Parser, GctfParser, StackParser, MontageParser


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
                for filename in file_list:
                    replace_dict = config.copy()
                    if self.depends:
                        filename = filename[len(config["lock_dir"]):]
                    stackname = pyfs.rext(filename, full=True)
                    replace_dict.update({
                        "filename": filename,
                        "filename_noex": pyfs.rext(
                            filename, full=True),
                        "filename_base": os.path.basename(filename),
                        "filename_directory": os.path.dirname(filename),
                        "filename_base_noext": pyfs.rext(
                            os.path.basename(filename), full=True),
                        "stackname": stackname
                    })

                    lock_filename = self.lock_lambda(stackname,
                                                     self.process_id, config)
                    done_filename = self.done_lambda(stackname,
                                                     self.process_id, config)
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

                        self.run_loop(config, replace_dict)

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
                    time.sleep(self.sleep)
                else:
                    idle = 0
                wait = True
            except KeyboardInterrupt:
                print("%s received Ctrl-C" % (self.process_id))
                return


class PreviewProcessor(CollectionProcessor):

    def __init__(self,
                 process_id,
                 config,
                 filename,
                 suffix="",
                 zoom=0.25,
                 **kwargs):
        CollectionProcessor.__init__(self, process_id, config, **kwargs)
        self.suffix = suffix
        self.zoom = zoom
        self.filename = filename

    def create_preview(self, filename):
        image = imaging.load(filename)[0]
        image = imaging.filters.norm(image, 0.01, 0.01, 0, 255)
        image = imaging.filters.zoom(image, self.zoom)
        picks_path = pyfs.rext(filename) + self.suffix + '.preview.png'
        imaging.save(image, picks_path)

    def run_loop(self, config, replace_dict):
        self.create_preview(
            string.Template(self.filename).substitute(replace_dict))


class CommandProcessor(CollectionProcessor):

    def __init__(self, process_id, process_command, config, **kwargs):
        CollectionProcessor.__init__(self, process_id, config, **kwargs)
        self.process_command = process_command

    def run_loop(self, config, replace_dict):
        command = Template(self.process_command).substitute(replace_dict)
        res = subprocess.run(command, shell=True)


def arguments():
    def floatlist(string):
        return list(map(float, string.split(',')))

    parser = argparse.ArgumentParser(
        description='Runs data processing live for incoming data')

    parser.add_argument('--init', default=None,
                        help='Initiates configuration file. Should be adjusted before starting')
    parser.add_argument('--list', default=False, action='store_true',
                        help='List available configuration templates')
    parser.add_argument(
        '--config', help='Configuration file to use', default="config.py")

    return parser.parse_args()


if __name__ == '__main__':

    args = arguments()
    print(args)
    config = {}
    processes = []
    if args.list:
        file_list = glob.glob(os.path.join(os.path.dirname(
            __file__), "collection_processor/config*.py"))
        for filename in file_list:
            print(os.path.basename(filename)[7:-3])
        sys.exit()

    if args.init is not None:
        try:
            with open(os.path.join(os.path.dirname(__file__), "collection_processor/config_" + args.init + ".py"), 'r') as config_file:
                template = string.Template(config_file.read())
        except IOError as e:
            print ("Config %s not found" % (args.init))
            sys.exit()
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

    parse_process = ParserProcess(config)

    for process in processes:
        process.start()
    parse_process.start()
    try:
        for process in processes:
            process.join()
        parse_process.join()
    except KeyboardInterrupt:
        print("Waiting for processes to finish")
        for process in processes:
            process.join()
        parse_process.join()
