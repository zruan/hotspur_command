import yaml
from pathlib import Path
from types import SimpleNamespace


config = None


def load_config(path):
    global config

    with open(path, 'r') as fp:
        config = yaml.safe_load(fp)

    config = SimpleNamespace(**config)
    config = _interpolate_config(config)
    _verify_config(config)

    return config


def get_config():
    global config

    if config is None:
        raise Exception('Hotspur config has not been loaded')
    else:
        return config


def _interpolate_config(config):
    config.couchdb_url = "http://{}:{}@{}:{}/couchdb/".format(
        config.admin_name,
        config.admin_pass,
        config.host,
        config.port
    )

    config.base_url = "http://{}:{}".format(
        config.host,
        config.port
    )

    log_dir = Path(config.data_path) / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    config.logfile = log_dir / f'{config.app_name}.log'

    config.search_patterns = [SimpleNamespace(glob=s['glob'], mask=s['mask'])
        for s in config.search_patterns]

    return config


def _verify_config(config):
    for p in config.search_patterns:
        glob_length = len(Path(p.glob).parts)
        mask_length = len(Path(p.mask).parts)
        assert glob_length == mask_length
