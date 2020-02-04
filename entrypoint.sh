#!/bin/bash

. /opt/conda/etc/profile.d/conda.sh
conda activate hotspur
python3 ./hotspur_command/hotspur.py "$@"
