import argparse

import hotspur_processor
import hotspur_reset
import hotspur_info
import hotspur_export

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Runs data processing live for incoming data'
    )
    parser.set_defaults(func=lambda _: parser.print_help())
    subparsers = parser.add_subparsers()

    process_parser = subparsers.add_parser(
        "process",
        help="Process data"
    )
    process_parser.set_defaults(func=lambda args: hotspur_processor.start_processing(args))
    process_parser.add_argument(
        '--dirs',
        help='Process all directories matching given directories',
        nargs='+'
    )

    export_parser = subparsers.add_parser("export")
    export_parser.set_defaults(func=lambda args: hotspur_export.export(args))
    export_parser.add_argument(
        '--hash',
        help="Hash of session to export",
        metavar='SESSION_HASH',
        required=True
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
    info_parser.set_defaults(func=lambda args: hotspur_info.show_info(args))
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
    info_parser.add_argument(
        '--config',
        help="Print the current configuration",
        action='store_true'
    )

    reset_parser = subparsers.add_parser(
        "reset",
        help="Delete databases using various strategies"
    )
    reset_parser.set_defaults(help_func=reset_parser.print_help)
    reset_parser.set_defaults(func=lambda args: hotspur_reset.reset(args))
    reset_parser.add_argument(
        '--all',
        help="Reset all sessions",
        action='store_true'
    )
    reset_parser.add_argument(
        '--search',
        help="Find and reset sessions using configured search settings",
        action='store_true'
    )
    reset_parser.add_argument(
        '--project',
        help="Reset sessions for project",
    )
    reset_parser.add_argument(
        '--dirs',
        help="Reset sessions matching given directories",
        nargs='+'
    )

    args = parser.parse_args()
    args.func(args)
