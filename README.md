# Welcome to Hotspur

Hotspur is a fully automated, real-time EM data preprocessing and monitoring tool.

Hotspur closes the gap between collecting EM data and seeing if that data is good, without adding extra burden to the microscopist. Hotspur automatically finds new sessions and data, extracts metadata, runs motion-correction and ctf-estimation, stitiches montages, and generates image previews.

The data and statistics are presented in a modern web view accessible from any browser. Using Hotspur, it's as easy to monitor data collection from home as it is from the micoscope workstation. Sharing is easy too: just pass along a url to the project or session. Hashed urls for projects and sessions mean that your data is private without needing to remember user accounts and passwords.

Hotspur is also simple to install. Using Conda and Docker, dependencies are nicely separated from your system. Hotspur does rely on MotionCor2, Ctffind4, and IMOD being installed separately, but you can point Hotspur to wherever these are installed on your system.

# Installation

- Install MotionCor2, Ctffind4, IMOD, Conda, Docker, Docker-Compose
- Pull down the Hotspur command repo: `git clone https://gitlab/hotspur/command`
- Create and configure Hotspur yaml config file: `python3 command/hotspur.py setup config`
- Create Conda environment file: `python3 command/hotspur.py setup conda`
- Create Conda environment: `conda env create -f environment.yml -p /path/to/conda/env`
- Create Docker-Compose file: `/path/to/conda/env/bin/python3 command/hotspur.py setup docker config.yml`
- Start Docker containers: `docker-compose -f docker-compose.yml -p hotspur -d up`
- Set up Couchdb via Fauxton
- Run Hotspur help message: `/path/to/conda/env/bin/python3 command/hotspur.py info`
