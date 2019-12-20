from pathlib import Path


template_dir_path = Path(__file__).parent / 'files'
utils.config_template_path = template_dir_path / 'hotspur-config.yml'
conda_env_template_path = template_dir_path / 'environment.yml'
docker_compose_template_path = template_dir_path / 'docker-compose.yml'


def load_hotspur_template():
    return _load_template(utils.config_template_path)


def load_conda_template():
    return _load_template(conda_env_template_path)


def load_docker_template():
    return _load_template(docker_compose_template_path)


def _load_template(path):
    name = path.name
    with open(path, 'r') as fp:
        template = fp.read()
    return template, name