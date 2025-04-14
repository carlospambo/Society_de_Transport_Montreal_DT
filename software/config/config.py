from pyhocon import ConfigFactory
from config.resources import resource_file_path
import logging


def load_config(config_file_name) -> dict:
    file_path = resource_file_path(config_file_name)
    config = ConfigFactory.parse_file(file_path)
    return config


def config_logger(logger_conf_file):
    logging.config.fileConfig(resource_file_path(logger_conf_file))


def config_logging(filename=None, level=logging.INFO):

    if filename is not None:
        # noinspection PyArgumentList
        logging.basicConfig(
            level=level,
            handlers=[logging.FileHandler(filename), logging.StreamHandler()],
            format='%(asctime)s.%(msecs)03d %(levelname)s %(name)s : %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # noinspection PyArgumentList
        logging.basicConfig(
            level=level,
            format='%(asctime)s.%(msecs)03d %(levelname)s %(name)s : %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
