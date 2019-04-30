import sys
import glob
import os
import argparse
import pyfs
import hashlib
import time

import couchdb

from processors import SessionProcessor, FramesFileProcessor, Motioncor2Processor, CtffindProcessor
import hotspur_setup


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
        '--target_dir',
        metavar='target-dir',
        help='A directory you want to process. This is for when you only want to process one session.'
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
    db = SessionProcessor.get_couchdb_database(
        session_data.user,
        session_data.grid,
        session_data.session
    )
    print('Deleting database "{}"...'.format(db.name))
    server.delete(db.name)
    print('Database deleted.')


def start_processing():
    args = arguments()

    # session_data = SessionProcessor.create_new_session(args.target_dir)
    # prepare_directory_structure(session_data)

    # if args.reset:
    #     reset_processing(session_data)
    #     exit()

    session_processor = SessionProcessor()
    frames_file_processor = FramesFileProcessor()
    motioncor2_processor = Motioncor2Processor()
    ctffind_processor = CtffindProcessor()

    while True:
        for session in session_processor.find_sessions(hotspur_setup.search_glob):
            print(session.frames_directory)
            exit()
            frames_file_processor.run(session)
            motioncor2_processor.run(session)
            ctffind_processor.run(session)
        time.sleep(5)
