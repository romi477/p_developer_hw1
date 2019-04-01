import sys, os, argparse
import gzip, bz2
import json
import re
import logging
from datetime import datetime
from collections import namedtuple, Counter
from statistics import mean, median


config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}

def set_logging(conf):
    logging.basicConfig(
        filename=conf.get('LOG_FILE'),
        filemode='w',
        level=conf.get('LOG_LEVEL', 'DEBUG'),
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S',
    )

def get_external_config():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', nargs='?', const='config.json')
    namespace = parser.parse_args()
    return namespace.config

def update_config(conf, conf_path):
    if os.path.exists(conf_path) and os.path.getsize(conf_path) > 0:
        try:
            with open(conf_path, 'r') as f:
                external_config = json.load(f)
        except Exception as ex:
            raise Exception(f"External config '{conf_path}' has not been read.\n{ex}")

        conf.update(external_config)
        print('Config has been successfully updated!')

    elif os.path.exists(conf_path) and os.path.getsize(conf_path) == 0:
        print(f"External config '{conf_path}' is empty, but it is OK!")
    else:
        raise FileNotFoundError(f"External config '{conf_path}' has not been found!")


def main():
    external_config_path = get_external_config()

    if external_config_path:
        update_config(config, external_config_path)

    set_logging(config)


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        # print('ERROR!!!', ex)
        logging.error(ex)
