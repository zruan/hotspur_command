from argparse import ArgumentParser
from subcommands.shared_parsers import config_file_parser, verbosity_parser


def run(args):
    # Import here to avoid loading unless needed
    from subcommands.info import main
    main.run(args)


parser = ArgumentParser(
    add_help=False,
    parents=[config_file_parser, verbosity_parser],
    description='retrieve info about projects and sessions',
)
parser.set_defaults(func=run)
parser.add_argument(
    '--all',
    help="summarize all projects",
    action='store_true'
)
parser.add_argument(
    '--hash',
    help="provide hash of given string",
    metavar="STRING"
)
parser.add_argument(
    '--project',
    help="provide info about a project",
)