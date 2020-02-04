import argparse


config_file_parser = argparse.ArgumentParser(add_help=False)
config_file_parser.add_argument(
    'config',
    help='the hotspur yaml configuration file',
    metavar='config'
)


verbosity_parser = argparse.ArgumentParser(add_help=False)
verbosity_parser.add_argument(
    '-v', '--verbose',
    action='count',
    default=0,
    help='increase stdout logging verbosity, and can be given more than once',
)