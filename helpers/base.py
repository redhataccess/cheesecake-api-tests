import configparser
import os


def config_reader(key, value):
    config = configparser.ConfigParser()
    config_file = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
    config.read(config_file)
    val = config[key][value]
    return val
