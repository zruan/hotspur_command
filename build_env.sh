#!/usr/bin/bash 

control_c(){
	deactivate
	exit
}

trap control_c SIGINT

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
