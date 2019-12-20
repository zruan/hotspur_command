from argparse import ArgumentParser
from subcommands.shared_parsers import config_file_parser, verbosity_parser


def run_hotspur_config(args):
    from subcommands.setup import hotspur_config
    utils.config.run(args)


def run_conda_config(args):
    # Import here to avoid loading unless needed
    from subcommands.setup import conda_config
    conda_config.run(args)


def run_docker_config(args):
    # Import here to avoid loading unless needed
    from subcommands.setup import docker_config
    docker_config.run(args)


parser = ArgumentParser(
    add_help=False,
    description='generate config files for setting up Hotspur',
)
subparsers = parser.add_subparsers()

config_parser = subparsers.add_parser(
    "config",
    help="generate a hotspur config file with default values",
)
config_parser.set_defaults(func=run_hotspur_config)

conda_parser = subparsers.add_parser(
    "conda",
    help="generate a conda environment.yml file",
)
conda_parser.set_defaults(func=run_conda_config)

docker_parser = subparsers.add_parser(
    "docker",
    help="Generate a docker-compose.yml file",
    parents=[config_file_parser]
)
docker_parser.set_defaults(func=run_docker_config)
