import yaml
import shutil
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
    return config


def _interpolate_config(config):
    config.couchdb_url = _get_couchdb_url(config)
    config.base_url = _get_base_url(config)
    config.logfile = _get_logfile(config)
    config.search_patterns = _namespace_search_patterns(config)
    config.imod_edmont_full_path = shutil.which(config.imod_edmont)
    config.imod_blendmont_full_path = shutil.which(config.imod_blendmont)
    config.imod_extractpieces_full_path = shutil.which(config.imod_extractpieces)
    config.motioncor2_full_path = shutil.which(config.motioncor2)
    config.ctffind_full_path = shutil.which(config.ctffind)
    return config


def _get_couchdb_url(config):
    return "http://{}:{}@{}:{}/couchdb/".format(
        config.admin_name,
        config.admin_pass,
        config.host,
        config.port
    )


def _get_base_url(config):
    return "http://{}:{}".format(
        config.host,
        config.port
    )


def _get_logfile(config):
    log_dir = Path(config.data_path) / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f'{config.app_name}.log'


def _namespace_search_patterns(config):
    def create_namespace(p):
        return SimpleNamespace(glob=p['glob'], mask=p['mask'])
    return [create_namespace(p) for p in config.search_patterns]


def _verify_config(config):
    for p in config.search_patterns:
        glob_length = len(Path(p.glob).parts)
        mask_length = len(Path(p.mask).parts)
        assert glob_length == mask_length
