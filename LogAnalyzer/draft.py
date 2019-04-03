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
    "LOG_DIR": "./log_"
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


def get_file_date(names, name='', date=''):
    for current_name in names:
        try:
            current_date = re.search(r'\d{8,}', current_name).group(0)
        except:
            continue
        if len(current_date) == 8 and current_date > date:
            name = current_name
            date = current_date
    return name, date

def find_last_log(conf):
    log_dir = conf['LOG_DIR']
    try:
        files = os.listdir(log_dir)
    except FileNotFoundError:
        logging.error(f"Logs directory '{log_dir}' does not exist!")
        return

    if not files:
        logging.info(f"Logs directory '{log_dir}' is empty!")
        return

    filter_files_gen = (file for file in files if re.match('nginx-access-ui', file))

    file, file_date = get_file_date(filter_files_gen)
    if not file:
        logging.info('No one log file for parsing has been found!')
        return

    file_ext = file.split('.')[-1]
    # if file_ext not in ['gz', 'bz2', f'log-{file_date}']:
    # if re.search(f'{file_ext}\s', f'gz bz2 log-{file_date}'):
    if re.search(file_ext, f'gz bz2 log-{file_date}'):
        logging.info(f"Found log file '{file}' has unsupported data format!")
        return

    try:
        parse_file_date = datetime.strptime(file_date, '%Y%m%d')
    except Exception as ex:
        logging.error(ex)
        return

    format_file_date = datetime.strftime(parse_file_date, '%Y.%m.%d')
    Logfile = namedtuple('Logfile', 'name date ext')
    log_file = Logfile(file, format_file_date, file_ext)
    logging.info(f"Required log file '{log_file}' has been found.")
    return log_file


def main():
    external_config_path = get_external_config()

    if external_config_path:
        update_config(config, external_config_path)

    set_logging(config)

    last_log = find_last_log(config)
    print(last_log)

if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        # print('ERROR!!!', ex)
        logging.error(ex)
