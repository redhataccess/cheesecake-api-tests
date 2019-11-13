import configparser
import os


def base_url():
    config = configparser.ConfigParser()
    config_file = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
    config.read(config_file)
    url = config['qa']['base_url']
    print("Base URL: {}".format(url))
    return url



