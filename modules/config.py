import configparser
import os


def get(section: str, key: str):
    config = configparser.ConfigParser()
    config.read('secrets.ini')
    return config.get(section, key)
