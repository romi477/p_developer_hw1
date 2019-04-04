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

def get_file_date(names):
    name = date = ''
    regex = r'nginx-access-ui.log-(\d{8})(?:\.tar.gz|\.tar.bz2)?$'
    for current_name in names:
        search = re.match(regex, current_name)
        if not search:
            continue
        if search[1] > date:
            name = current_name
            date = search[1]
    return name, date

def find_last_log(conf):
    log_dir = conf['LOG_DIR']
    try:
        files = os.listdir(log_dir)
        print(type(files))
    except FileNotFoundError:
        logging.error(f"Logs directory '{log_dir}' does not exist!")
        return

    if not files:
        logging.info(f"Logs directory '{log_dir}' is empty!")
        return

    file, file_date = get_file_date(files)
    if not file:
        logging.info('No one log file for parsing has been found!')
        return

    try:
        parse_file_date = datetime.strptime(file_date, '%Y%m%d')
    except Exception as ex:
        logging.error(ex)
        return

    format_file_date = datetime.strftime(parse_file_date, '%Y.%m.%d')
    Logfile = namedtuple('Logfile', 'name date')
    log_file = Logfile(file, format_file_date)
    logging.info(f"Required log file '{log_file}' has been found.")
    return log_file


def parse_string(stri):
    decode_stri = stri.decode('utf-8')
    try:
        url = decode_stri.split('HTTP')[0].split()[-1]
        query_time = float(decode_stri.rsplit(maxsplit=1)[-1])
    except Exception as ex:
        logging.error(ex)
        return
    StriParse = namedtuple('StriParse', 'url query_time')
    return StriParse(url, query_time)

def serialize_data(urls_dict, parsed_queries, parsed_queries_time, fails, key, value):
    count = len(urls_dict[key])
    count_perc = count * 100 / (parsed_queries + fails)
    time_perc = value * 100 / parsed_queries_time
    time_avg = mean(urls_dict[key])
    time_max = max(urls_dict[key])
    time_med = median(urls_dict[key])

    report_url = {
        'url': key,
        'time_sum': round(value, 3),
        'count': count,
        'count_perc': round(count_perc, 3),
        'time_perc': round(time_perc, 3),
        'time_avg': round(time_avg, 3),
        'time_max': round(time_max, 3),
        'time_med': round(time_med, 3),
    }
    return report_url

def log_parser(log_file, conf):
    urls_dict = {}
    report_urls_list = []
    counter_urls = Counter()
    parsed_queries, parsed_queries_time, fails = 0, 0, 0

    operator = gzip.open if log_file.name.endswith('gz') else bz2.open if log_file.name.endswith('bz2') else open
    with operator(os.path.join(conf['LOG_DIR'], log_file.name), 'rb') as file:
        for stri in (s for s in file):
            stri_parse = parse_string(stri)
            if not stri_parse:
                fails += 1
                continue
            parsed_queries += 1
            parsed_queries_time += stri_parse.query_time
            counter_urls[stri_parse.url] += stri_parse.query_time
            urls_dict.setdefault(stri_parse.url, []).append(stri_parse.query_time)

    if fails * 100 / (parsed_queries + fails) >= conf.get('TOTAL_FAILS', 51):
        logging.info('Number of failed operations exceeded the allowed threshold!')
        return

    for key, value in counter_urls.most_common(conf['REPORT_SIZE']):
        report_url = serialize_data(urls_dict, parsed_queries, parsed_queries_time, fails, key, value)
        report_urls_list.append(report_url)
    logging.info('Parsing has been successfully completed.')
    return report_urls_list


def generate_report(parsed_list, report_name, template_name):
    try:
        with open(template_name, 'r', encoding='utf-8') as file:
            read_template = file.read()
    except Exception as ex:
        logging.error(ex)
        return

    report = read_template.replace('$table_json', str(parsed_list))
    try:
        with open(report_name, 'w') as file:
            file.write(report)
    except Exception as ex:
        logging.error(ex)
        return

    logging.info(f"Report '{report_name}' has been successfully dumped.")
    return True


def main():
    external_config_path = get_external_config()

    if external_config_path:
        update_config(config, external_config_path)

    set_logging(config)

    last_log = find_last_log(config)

    if not last_log:
        sys.exit('Forced termination!')

    report_path = os.path.join(config['REPORT_DIR'], f'report-{last_log.date}.html')
    if os.path.exists(config['REPORT_DIR']):
        if os.path.exists(report_path):
            logging.info(f"Required report '{report_path}' already exists.")
            sys.exit('Forced termination!')
    else:
        os.makedirs(config['REPORT_DIR'])

    parsed_list = log_parser(last_log, config)
    if not parsed_list:
        sys.exit('Forced termination!')

    template_name = 'report.html'
    if not os.path.exists(template_name):
        logging.error(f"Report template '{template_name}' has not been found!")
        sys.exit('Emergency stop!')

    status = generate_report(parsed_list, report_path, template_name)
    if not status:
        sys.exit('Emergency stop!')
    logging.info('Script has been completed.')


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        logging.error(ex)