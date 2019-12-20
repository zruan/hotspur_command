from argparse import ArgumentParser
from subcommands.shared_parsers import config_file_parser, verbosity_parser


def run(args):
    # Import here to avoid loading unless needed
    from subcommands.prune import main
    main.run(args)


parser = ArgumentParser(
    add_help=False,
    parents=[config_file_parser, verbosity_parser],
    description='Remove database entries for projects or sessions',
)
parser.set_defaults(func=run)
parser.add_argument(
    '--all',
    help="reset all projects and sessions",
    action='store_true'
)
parser.add_argument(
    '--project',
    help="reset all sessions for project",
    metavar='NAME',
)
parser.add_argument(
    '--session',
    help="reset session",
    metavar='HASH',
)