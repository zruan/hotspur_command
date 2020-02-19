from argparse import ArgumentParser
from subcommands.shared_parsers import config_file_parser, verbosity_parser


def run(args):
    # Import here to avoid loading unless needed
    from subcommands.export import main
    main.run(args)


parser = ArgumentParser(
    add_help=False,
    parents=[config_file_parser, verbosity_parser],
    description='Export processed data and metadata for further use in Relion',
)
parser.set_defaults(func=run)
parser.add_argument(
    'hash',
    help="hash of session to export",
)
parser.add_argument(
    '--out-dir',
    help="directory in which output will be placed. Defaults to .../hotspur-data/export/session-hash"
)