import pyfs
import glob
import string
import traceback

class Parser:
    def __init__(self, parser_id, database, config, global_config, db):
        self.parser_id = parser_id
        self.database = database
        self.config = config
        self.global_config = global_config
        self.db = db
        if "glob" in config:
            self.glob = string.Template(config["glob"]).substitute(global_config)
        elif "depends" in config:
            self.glob = (
                global_config["lock_dir"] + pyfs.rext(global_config["glob"]) +
                "." + config["depends"] + ".done")
        else:
            raise ValueError(
                self.parser_id +
                ": Need to specify either watch_glob or dependency")

    def parse(self):
        num_files = 0
        files = glob.glob(self.glob)
        for filename in files:
            if "depends" in self.config:
                filename = filename[len(self.global_config["lock_dir"]):-len(".done")]
            if "stackname_lambda" in self.config:
                stackname = self.config["stackname_lambda"](filename,self.global_config)
            else:
                stackname = pyfs.rext(filename, full=False)
            if  ("run_once" not in self.config or self.config["run_once"]) and stackname in self.database and self.parser_id in self.database[
                    stackname]:
                continue
            if stackname not in self.database:
                self.database[stackname] = {}
            print("%s: Parsing %s ..." % (self.parser_id, stackname))
            try:
                self.parse_process(stackname)
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except:
                with open("parse_error.log", 'a') as fp:
                    traceback.print_exc(file=fp)
            num_files += 1
            print("Done!")
            if ("num_files_max" in self.config and num_files >=
                    self.config["num_files_max"]) or num_files > 500:
                break
        return num_files