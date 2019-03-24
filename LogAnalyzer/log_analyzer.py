import os, sys, argparse
import gzip, bz2
import json
import re
import logging
from datetime import datetime
from collections import namedtuple, Counter, OrderedDict
from statistics import mean, median
from pprint import pprint


config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}

def set_logging(config):
    logging.basicConfig(
        filename=config.get('LOG_FILE'),
        filemode='w',
        level=config.get('LOG_LEVEL', 'DEBUG'),
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S',
    )


def get_external_config():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', nargs='?', const='config.json')
    namespace = parser.parse_args()
    return namespace.config

def update_config(config, config_path):
    if os.path.exists(config_path) and os.path.getsize(config_path) > 0:
        try:
            with open(config_path, 'r') as f:
                external_config = json.load(f)
        except json.decoder.JSONDecodeError:
            return False, f"External config '{config_path}' has not been parsed!"
        config.update(external_config)
        return True, 'Config has been successfully updated!'
    elif os.path.exists(config_path) and os.path.getsize(config_path) == 0:
        return True, f"External config '{config_path}' is empty, but it is OK!"
    else:
        return False, f"External config '{config_path}' has not been found!"

def find_last_log(config):
    log_dir = config['LOG_DIR']
    try:
        files_iterator = os.listdir(log_dir)
    except FileNotFoundError:
        return False, f"Logs directory '{log_dir}' does not exist!"
    if not files_iterator:
        return False, f"Logs directory '{log_dir}' is empty!"
    files_dict = {re.search(r'\d{8}', name).group(0): name for name in files_iterator if 'nginx-access-ui' in name}
    if not files_dict:
        return False, 'No one log file for parsing has been found!'
    last_date = sorted(list(files_dict.keys()))[-1]
    parse_last_date = datetime.strptime(last_date, '%Y%m%d')
    format_last_date = datetime.strftime(parse_last_date, '%Y.%m.%d')
    Logfile = namedtuple('Logfile', 'name date')
    last_log = Logfile(files_dict[last_date],format_last_date)
    return last_log, 'Required log file has been found!'


def parse_log(log_file, config):
    ext = log_file.name.split('.')[-1]
    operator = gzip.open if ext == 'gz' else bz2.open if ext == 'bz2' else open

    with operator(os.path.join(config['LOG_DIR'], log_file.name), 'rb') as file:
        log_gen = (i for i in file)

        urls_dict = {}
        total_queries, total_queries_time, fails = 0, 0, 0
        counter_urls = Counter()
        report_urls_dict = OrderedDict()

        for log_str in log_gen:
            log_str = log_str.decode()
            try:
                url = log_str.split('HTTP')[0].split()[-1]
                query_time = float(log_str.split()[-1])
            except Exception as ex:
                print(ex)
                print('----------------')
                print(log_str)
                print('----------------')
                fails += 1
                continue
            counter_urls[url] += query_time

            urls_dict.setdefault(url, [])
            urls_dict[url].append(query_time)

            total_queries += 1
            total_queries_time += query_time

        print('counter: ', sys.getsizeof(counter_urls))
        print('urls dict: ', sys.getsizeof(urls_dict))
        print('fails: ', fails)


        for key, value in counter_urls.most_common(1000):
            count = len(urls_dict[key])
            count_perc = (count / total_queries) * 100
            time_perc = (value / total_queries_time) * 100
            time_avg = mean(urls_dict[key])
            time_max = max(urls_dict[key])
            time_med = median(urls_dict[key])

            report_urls_dict[key] = {
                'count': count,
                'count_perc': round(count_perc, 3),
                'time_perc': round(time_perc, 3),
                'time_avg': round(time_avg, 3),
                'time_max': round(time_max, 3),
                'time_med': round(time_med, 3),
            }

        pprint(report_urls_dict)
        print('report dict: ', sys.getsizeof(report_urls_dict))



def main():
    config_path = get_external_config()
    if config_path:
        status, message = update_config(config, config_path)
        print(message)
        if not status:
            sys.exit('Emergency stop!')

    set_logging(config)

    last_log, message = find_last_log(config)
    logging.info(message)
    if not last_log:
        sys.exit('Forced termination. No tasks!')
    logging.info(last_log)

    parse_log(last_log, config)



if __name__ == "__main__":
    main()

