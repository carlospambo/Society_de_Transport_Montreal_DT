import os
import logging.config
from pyhocon import ConfigFactory

def resource_file_path(filename):
    python_path = os.environ.get("PYTHONPATH")
    if python_path is None:
        directories = ['.']
    else:
        directories = python_path.split(os.pathsep) + ['.']

    for d in directories:
        filepath = os.path.join(d, filename)
        if os.path.exists(filepath):
            return filepath

    print(f"File not found: {filename}")
    print("Tried the following directories:")
    print(directories)
    raise ValueError(f"File not found: {filename}")


def load_config(config_file_name) -> dict:
    file_path = resource_file_path(config_file_name)
    config = ConfigFactory.parse_file(file_path)
    return config

def config_logger(logger_conf_file):
    logging.config.fileConfig(resource_file_path(logger_conf_file))