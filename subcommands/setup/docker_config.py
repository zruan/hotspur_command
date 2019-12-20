from pathlib import Path

from utils.config import load_config
from templates.loader import load_docker_template


def run(args):
    config = load_config(args.config)
    template, name = load_docker_template()
    contents = template.format(**vars(config))

    destination = Path() / name
    with open(destination, 'w') as fp:
        fp.write(contents)
    print(f'Saved {destination.resolve()}')

    print('')
    print("Start the docker containers using a command such as:")
    print(f'docker-compose -p {config.app_name} -f {name} up')
    print('')
