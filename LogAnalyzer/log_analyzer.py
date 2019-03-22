import os, sys
import gzip, bz2
import re
import json
import logging
from datetime import datetime
from collections import namedtuple




config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log2"
}

def set_logging(config):
    logging.basicConfig(
        filename=config.get('LOG_FILE'),
        filemode='w',
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S',
    )


def update_config(config):
    config_path = './config.json'
    if sys.argv[1] == '--config':
        try:
            config_path = sys.argv[2]
        except IndexError:
            pass
    else:
        return False, f"Wrong command argument '{sys.argv[1]}'"
    if os.path.splitext(config_path)[-1].lower() != '.json':
        return False, f"External-config '{config_path}' not a JSON!"
    if os.path.exists(config_path) and os.path.getsize(config_path) > 0:
        try:
            with open(config_path, 'r') as f:
                external_config = json.load(f)
        except json.decoder.JSONDecodeError:
            return False, f"External-config '{config_path}' has not been parsed!"
        config.update(external_config)
        return True, 'Config has been successfully updated!'
    elif os.path.exists(config_path) and os.path.getsize(config_path) == 0:
        return True, f"External-config '{config_path}' is empty, but it is OK!"
    else:
        return False, f"External-config '{config_path}' has not been found!"

def find_last_log(config):
    log_dir = config['LOG_DIR']
    if not os.listdir(log_dir):
        return False, 'Log-directory is empty.'
    files_dict = {re.search(r'\d{8}', line).group(0): line for line in next(os.walk(log_dir))[-1] if
                  'nginx-access-ui' in line}
    if not files_dict:
        return False, 'No one log-file for parsing has been found!'
    last_date = sorted(list(files_dict.keys()))[-1]
    parse_last_date = datetime.strptime(last_date, '%Y%m%d')
    format_last_date = datetime.strftime(parse_last_date, '%Y.%m.%d')
    extension = files_dict[last_date].split('.')[-1].lower()
    Loginfo = namedtuple('Loginfo', 'log_name extension date')
    last_log = Loginfo(files_dict[last_date], extension, format_last_date)
    return last_log, 'Required log-file has been found!'


def main():
    if len(sys.argv) > 1:
        status, info = update_config(config)
        print(info)
        if not status:
            sys.exit('Something went wrong! Exit!')
    set_logging(config)

    logging.info(config)

    last_log, info = find_last_log(config)
    if not last_log:
        logging.error(info)
        sys.exit('Something went wrong! Exit!')
    logging.info(info)
    logging.info(last_log)



if __name__ == "__main__":
    main()

