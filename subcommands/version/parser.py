from argparse import ArgumentParser
from subcommands.shared_parsers import config_file_parser, verbosity_parser

def run(args):
    print("0.9.1")

parser = ArgumentParser(
    add_help=False,
    parents=[config_file_parser, verbosity_parser],
    description='print current version',
)
parser.set_defaults(func=run)
