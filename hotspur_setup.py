import argparse
import shutil
from pathlib import Path

import hotspur_config


template_dir_path = Path(__file__).parent / 'config_templates'


def prepare_hotspur_config():
    source = template_dir_path / 'hotspur-config.yml'
    destination = Path() / 'hotspur-config.yml'
    copy_template(source, destination)


def prepare_conda_config():
    source = template_dir_path / 'environment.yml'
    destination = Path() / 'environment.yml'
    copy_template(source, destination)

    print('\n'.join([
        '',
        'Create the conda environment using a command such as:',
        'conda env create -f environment.yml -p /conda/env/path',
        ''
    ]))


def prepare_docker_config(args):
    config = hotspur_config.load_config(args.config_file)
    # config = flatten(config)
    source = template_dir_path / 'docker-compose.yml'

    with open(source, 'r') as fp:
        contents = fp.read()
    
    contents = contents.format(**vars(config))

    destination = Path() / 'hotspur-docker-compose.yml'
    with open(destination, 'w') as fp:
        fp.write(contents)
    print(f'Saved {destination}')

    print('\n'.join([
        '',
        "Start the docker containers using a command such as:",
        f'docker-compose -p {config.app_name} -f docker-compose.yml up',
        ''
    ]))


def copy_template(source, destination):
    # if destination.exists():
    #     overwrite = input(f'The file {destination} alread exists.\nOverwrite? [Y/n] ')
    #     if overwrite is '' or overwrite in ['y', 'Y']:
    #         pass
    #     elif overwrite in ['n', 'N']:
    #         print('NOT overwritting file. Exiting.')
    #         return
    #     else:
    #         print(f"Expected [' ', 'y', 'Y', 'n', 'N'] but got {overwrite}. Exiting.")
    #         return

    copy(source, destination)
    print(f'Saved {destination}')

# https://stackoverflow.com/questions/33625931/copy-file-with-pathlib-in-python
def copy(src_path, dst_path):
    return shutil.copy2(str(src_path), str(dst_path))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description =' '.join([
            "Provides some assistant for setting up various facets of hotspur. To run hotspur:",
            "1) A conda environment with the necessary packages must be active when starting hotspur",
            "2) Docker containers for the database and web resources must be running",
            "3) A hotspur config file must be passed to hotspur when starting"
        ])
    )
    parser.set_defaults(func=lambda _: parser.print_help())
    subparsers = parser.add_subparsers()


    conda_parser = subparsers.add_parser(
        "conda",
        help=' '.join([
            "Generate a conda environment.yml file.",
            "The environment file can be used to create the hotspur conda environment.",
        ])
    )
    conda_parser.set_defaults(func=lambda _: prepare_conda_config())


    config_parser = subparsers.add_parser(
        "config",
        help=' '.join([
            "Generate a hotspur config file with default values.",
            "This config file is well-commented and describes what all of the fields do."
        ])
    )
    config_parser.set_defaults(func=lambda _: prepare_hotspur_config())


    docker_parser = subparsers.add_parser(
        "docker",
        help=' '.join([
            "Generate a docker-compose.yml file to orchestrate the hotspur Docker containers.",
            "The hotspur config file is necessary for this to properly set up the ports, etc.",
            "These containers do not need to run on the same system as the hotspur backend."
        ])
    )
    docker_parser.set_defaults(func=lambda args: prepare_docker_config(args))
    docker_parser.add_argument(
        'config_file',
        help="The hotspur config yaml file",
        metavar='CONFIG_FILE'
    )

    args = parser.parse_args()
    args.func(args)
