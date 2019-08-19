import argparse

import hotspur_processor
import hotspur_reset

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Runs data processing live for incoming data'
    )
    parser.set_defaults(func=lambda _: parser.print_help())
    subparsers = parser.add_subparsers()

    process_parser = subparsers.add_parser(
        "process",
        help="This is some help"
    )
    process_parser.set_defaults(func=lambda args: hotspur_processor.start_processing(args))
    process_parser.add_argument(
        '--dirs',
        help='Process all directories matching given directories',
        nargs='+'
    )

    # export_parser = subparsers.add_parser("export")
    # export_parser.set_defaults(func=lambda args: print(args))

    # hash_parser = subparsers.add_parser("hash")
    # hash_parser.set_defaults(func=lambda args: print(args))

    # list_parser = subparsers.add_parser("list")
    # list_parser.set_defaults(func=lambda args: print(args))

    reset_parser = subparsers.add_parser(
        "reset",
        help="Reset sessions by clearing the session database. By default, "
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
        help="Reset sessions for project"
    )
    reset_parser.add_argument(
        '--dirs',
        help="Reset sessions matching given directories",
        nargs='+'
    )

    args = parser.parse_args()
    args.func(args)
