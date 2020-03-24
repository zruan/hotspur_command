import argparse

from subcommands.setup.parser   import parser as setup_parser
from subcommands.export.parser  import parser as export_parser
from subcommands.info.parser    import parser as info_parser
from subcommands.process.parser import parser as process_parser
from subcommands.prune.parser   import parser as prune_parser
from subcommands.version.parser   import parser as version_parser



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Runs data processing live for incoming data'
    )
    subparsers = parser.add_subparsers()

    subparsers.add_parser(
        name='setup',
        help='Generate config files for setting up Hotspur',
        parents=[setup_parser]
    )
    subparsers.add_parser(
        name='process',
        help='Automatically find and process EM data',
        parents=[process_parser]
    )
    subparsers.add_parser(
        name='info',
        help='Retrieve info about projects and sessions',
        parents=[info_parser]
    )
    subparsers.add_parser(
        name='export',
        help='Export data alongside Relion metadata star files',
        parents=[export_parser]
    )
    subparsers.add_parser(
        name='prune',
        help='Remove processed data and databases for projects or sessions',
        parents=[prune_parser]
    )
    subparsers.add_parser(
        name='version',
        help='Print the current version',
        parents=[version_parser]
    )

    args = parser.parse_args()

    if 'config' in args:
        from utils.config import load_config
        load_config(args.config)

    if 'func' in args:
        args.func(args)
    else:
        parser.print_help()
