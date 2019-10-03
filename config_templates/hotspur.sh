#!/bin/bash

SCRIPT_DIR=$(dirname $(realpath $0))
HOTSPUR_PATH="${SCRIPT_DIR}/hotspur.py"

main() {
    # This lets us use 'conda activate' in a script
    # https://github.com/conda/conda/issues/7980
    eval "$(conda shell.${SHELL} hook)"

    conda activate "hotspur"

    # This makes sure the conda environment is deactivated when we're done
    trap cleanup EXIT

    python3 "$HOTSPUR_PATH" "$@"

    cleanup
}

cleanup() {
	conda deactivate
}

main "$@"; exit