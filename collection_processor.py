import sys
import glob
import os
import argparse
import pyfs
import hashlib
import time

import couchdb

from processors import CommandProcessor, PreviewProcessor, IdogpickerProcessor
from processors import FramesFileProcessor, Motioncor2Processor
from collection_parser import IdogpickerParser, ParserProcess, MotionCor2Parser, GctfParser, CtffindParser, MontageParser, PickParser, NavigatorParser
from parsers.stack_parser import StackParser
import hotspur_setup
import hotspur_initialize


parsers = {
    # "MotionCor2" : {
    #     "type" : MotionCor2Parser,
    #     "depends" : "motioncor2",
    #     "sum_micrograph" : "${base}_mc.mrc",
    #     "dw_micrograph" : "${base}_mc_DW.mrc",
    #     "log" : "${base}_mc.log",
    #     "preview" : "${base}_mc_DW.preview.png"
    # },
    # "Gctf" : {
    #     "type" : GctfParser,
    #     "depends" : "gctf",
    #     "ctf_image" : "${base}_mc_DW.ctf",
    #     "ctf_image_preview" : "${base}_mc_DW_ctf.preview.png",
    #     "ctf_star" : "${base}_mc_DW_gctf.star",
    #     "ctf_epa_log" : "${base}_mc_DW_EPA.log",
    #     "ctf_log" : "${base}_mc_DW_gctf.log"
    # },
    # "ctffind4" : {
    #     "type" : CtffindParser,
    #     "depends" : "ctffind",
    #     "ctf_image" : "${base}_mc_DW_ctffind.ctf",
    #     "ctf_image_preview" : "${base}_mc_DW_ctffind_ctf.preview.png",
    #     "ctf_epa_log" : "${base}_mc_DW_ctffind_avrot.txt",
    #     "ctf_log" : "${base}_mc_DW_ctffind.txt"
    # },
    "moviestack" : {
        "type": StackParser,
        "depends" : "motioncor2",
        "moviestack" : "${collection_dir}${base}.tif"
    },
    # "navigator" : {
    #     "type": NavigatorParser,
    #     "glob" : "${collection_dir}*.nav",
    #     "stackname_lambda" : lambda x, config : pyfs.rext(x[len(config["collection_dir"]):],full=True),
    #     "navigatorfile" : "${collection_dir}${base}.nav",
    #     "run_once" : True
    # },
    # "idogpicker" : {
    #     "type": IdogpickerParser,
    #     "depends" : "idogpicker",
    #     "filename" : "${base}_mc_DW.idogpicker.json"
    # },
    # "montage" : {
    #     "type": MontageParser,
    #     "glob" : "${lock_dir}/*.montage.done",
    #     "stackname_lambda" : lambda x, config : pyfs.rext(x[len(config["lock_dir"]):],full=True),
    #     "montage" : "${collection_dir}${base}.mrc"
    # },
    "Database" : "data.json"
}


# def get_user_id_hash(user_id):
#     m = hashlib.md5()
#     m.update(user_id.encode('utf-8'))
#     m.update(hotspur_setup.hash_salt.encode('utf-8'))
#     digest = m.hexdigest()
#     print("User ID hash is: {0}".format(digest))
#     return digest

def prepare_directory_structure(session_data):
    if not os.path.exists(session_data.processing_directory):
        os.makedirs(session_data.processing_directory)

def arguments():
    parser = argparse.ArgumentParser(
        description='Runs data processing live for incoming data'
    )
    parser.add_argument(
        'target_dir',
        metavar='target-dir',
        help='The directory containing your data.'
    )
    parser.add_argument(
        '--reset',
        help="Remove all '.done' files that track processing progress.",
        action='store_true'
    )
    return parser.parse_args()


def prepare_gain_reference(gain_ref, scratch_dir):
    print(gain_ref)
    # gain_ref =  os.path.normpath()
    _, ext = os.path.splitext(gain_ref)
    target_filename = "gainRef.mrc"
    target_path = os.path.join(scratch_dir, target_filename)

    if not os.path.exists(target_path):
        if ext == '.mrc':
            os.system("cp {} {}".format(gain_ref, target_path))
        elif ext == '.dm4':
            os.system("dm2mrc {} {}".format(gain_ref, target_path))
        else:
            raise ValueError('Gain reference is not ".dm4" or ".mrc" format.')

    return target_path


def reset_processing(session_data):
    print("Removing '.done' files...")
    for file in os.listdir(session_data.processing_directory):
        if file.endswith('.done'):
            file_path = os.path.join(session_data.processing_directory, file)
            os.remove(file_path)
    print("Successfully removed '.done' files.")

    server = couchdb.Server(hotspur_setup.couchdb_address)
    db = hotspur_initialize.get_couchdb_database(
        session_data.user,
        session_data.grid,
        session_data.session
    )
    print('Deleting database "{}"...'.format(db.name))
    server.delete(db.name)
    print('Database deleted.')


def start_processing():
    args = arguments()

    session_data = hotspur_initialize.get_session_data(args.target_dir)
    prepare_directory_structure(session_data)

    if args.reset:
        reset_processing(session_data)
        exit()

    frames_file_processor = FramesFileProcessor()
    motioncor2_processor = Motioncor2Processor()

    while True:
        frames_file_processor.run(session_data)
        motioncor2_processor.run(session_data)
        time.sleep(5)

#     config['gain_ref'] = prepare_gain_reference(config['gain_ref'], config['scratch_dir'])


#     if args.reset:
#         reset_processing(config)
#         sys.exit()

#     ref_path = prepare_gain_reference(
#         config['gain_ref'], config['scratch_dir'])
#     config['gainref'] = ref_path

#     config['parser'] = parsers
#     parse_process = ParserProcess(config)

#     for process in processes:
#         process.start()
#     parse_process.start()

#     try:
#         for process in processes:
#             process.join()
#         parse_process.join()
#     except KeyboardInterrupt:
#         print("Waiting for processes to finish")
#         for process in processes:
#             process.join()
#         parse_process.join()

# if __name__ == '__main__':
#     start_processing()
