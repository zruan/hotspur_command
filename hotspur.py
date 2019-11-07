import argparse
import hotspur_config

def process(args):
    import hotspur_processor
    hotspur_processor.start_processing(args)

def reset(args):
    import hotspur_reset
    hotspur_reset.reset(args)

def info(args):
    import hotspur_info
    hotspur_info.main(args)

def export(args):
    import hotspur_export
    hotspur_export.export(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Runs data processing live for incoming data'
    )
    parser.add_argument(
        'config_file',
        help='The hotspur yaml configuration file',
        metavar='config',
    )
    parser.set_defaults(func=lambda _: parser.print_help())
    subparsers = parser.add_subparsers()



    process_parser = subparsers.add_parser(
        "process",
        help="Process data"
    )
    process_parser.set_defaults(help_func=process_parser.print_help)
    process_parser.set_defaults(func=process)
    process_parser.add_argument(
        '--dirs',
        help='Process all directories matching given directories',
        nargs='+'
    )



    export_parser = subparsers.add_parser("export")
    export_parser.set_defaults(help_func=export_parser.print_help)
    export_parser.set_defaults(func=export)
    export_parser.add_argument(
        'hash',
        help="Hash of session to export",
        metavar='SESSION_HASH',
    )
    export_parser.add_argument(
        '--out',
        dest='out_dir',
        help="Directory in which output will be place"
    )



    info_parser = subparsers.add_parser(
        "info",
        help="Provide info about projects and hotspur config"
    )
    info_parser.set_defaults(help_func=info_parser.print_help)
    info_parser.set_defaults(func=info)
    info_parser.add_argument(
        '--all',
        help="Summarize all projects",
        action='store_true'
    )
    info_parser.add_argument(
        '--hash',
        help="Provide hash of given string",
        metavar="STRING"
    )
    info_parser.add_argument(
        '--project',
        help="Provide info about a project",
    )



    reset_parser = subparsers.add_parser(
        "reset",
        help="Delete databases using various strategies"
    )
    reset_parser.set_defaults(help_func=reset_parser.print_help)
    reset_parser.set_defaults(func=reset)
    reset_parser.add_argument(
        '--all',
        help="Reset all projects and sessions",
        action='store_true'
    )
    reset_parser.add_argument(
        '--project',
        help="Reset all sessions for project with given name",
        metavar='PROJECT_NAME',
    )
    reset_parser.add_argument(
        '--session',
        help="Reset session with given hash",
        metavar='SESSION_HASH',
    )



    args = parser.parse_args()
    hotspur_config.load_config(args.config_file)
    args.func(args)

