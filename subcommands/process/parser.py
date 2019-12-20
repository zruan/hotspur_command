import argparse
from subcommands.shared_parsers import config_file_parser, verbosity_parser


def run(args):
    # Import here to avoid loading unless needed
    from subcommands.process import main
    main.run(args)


parser = argparse.ArgumentParser(
    add_help=False,
    parents=[config_file_parser, verbosity_parser],
    description="process data and metadata using MotionCor2, Ctffind4, and IMOD"
)
parser.set_defaults(func=run)