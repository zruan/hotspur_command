import argparse
import hotspur_processor

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

    # reset_parser = subparsers.add_parser("reset")
    # reset_parser.set_defaults(func=lambda args: print(args))
    # reset_parser.add_argument(
    #     '--all',
    #     dest='reset_all',
    #     help="Reset all projects",
    #     action='store_true'
    # )
    # reset_parser.add_argument(
    #     '--project',
    #     dest='project_to_reset',
    #     help="Reset all sessions for project with given name"
    # )
    # reset_parser.add_argument(
    #     '--dirs',
    #     dest='dirs_to_reset',
    #     help="Reset all processing done for given directories",
    #     nargs='+'
    # )
    # reset_parser.add_argument(
    #     '--search',
    #     dest='reset_found_sessions',
    #     help="Reset all processing done for sessions found by hotspur",
    #     action='store_true'
    # )

    args = parser.parse_args()
    args.func(args)
