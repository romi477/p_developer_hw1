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
    log_ext = files_dict[last_date].split('.')[-1]
    allowed_extensions = ['gz', 'bz2', f'log-{last_date}']
    if log_ext not in allowed_extensions:
        return False, 'Found log file has unsupported data format!'
    parse_last_date = datetime.strptime(last_date, '%Y%m%d')
    format_last_date = datetime.strftime(parse_last_date, '%Y.%m.%d')
    operator = gzip.open if log_ext == 'gz' else bz2.open if log_ext == 'bz2' else open
    Logfile = namedtuple('Logfile', 'name date operator')
    last_log = Logfile(files_dict[last_date], format_last_date, operator)
    return last_log, 'Required log file has been found!'


def log_parser(log_file, config):
    with log_file.operator(os.path.join(config['LOG_DIR'], log_file.name), 'rb') as file:
        string_generator = (i for i in file)

        urls_dict = {}
        counter_urls = Counter()
        report_urls_dict = OrderedDict()
        parsed_queries, parsed_queries_time, fails = 0, 0, 0

        for str_i in string_generator:
            str_i = str_i.decode()
            try:
                url = str_i.split('HTTP')[0].split()[-1]
                query_time = float(str_i.split()[-1])
            except Exception as ex:
                logging.error(ex)
                fails += 1
                continue
            counter_urls[url] += query_time
            urls_dict.setdefault(url, []).append(query_time)

            parsed_queries += 1
            parsed_queries_time += query_time

        print('fails: ', fails)
        print('total queries :', parsed_queries)

        if fails * 100 / (parsed_queries + fails) >= config.get('TOTAL_FAILS', 51):
            return False, 'Number of failed operations exceeded the allowed threshold!'

        UrlInfo = namedtuple('UrlInfo', 'count count_perc time_sum time_perc time_avg time_max time_med')

        for key, value in counter_urls.most_common(config['REPORT_SIZE']):
            count = len(urls_dict[key])
            count_perc = count * 100 / (parsed_queries + fails)
            time_sum = value
            time_perc = value * 100 / parsed_queries_time
            time_avg = mean(urls_dict[key])
            time_max = max(urls_dict[key])
            time_med = median(urls_dict[key])

            settings = [count, count_perc, time_sum, time_perc, time_avg, time_max, time_med]
            settings = list(map(lambda x: round(x, 3), settings))

            report_urls_dict[key] = UrlInfo(*settings)

        pprint(report_urls_dict)




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

    log_parser(last_log, config)



if __name__ == "__main__":
    main()

