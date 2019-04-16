import sys, os, argparse
import gzip
import json
import re
import logging
from datetime import datetime
from copy import deepcopy
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
    parser.add_argument('--config', nargs='?', default='config.json')
    namespace = parser.parse_args()
    return namespace.config


def update_config(conf, ext_conf):
    if os.path.exists(ext_conf) and os.path.getsize(ext_conf) > 0:
        try:
            with open(ext_conf, 'r') as f:
                extended_config = json.load(f)
        except Exception as ex:
            raise Exception(f"External config '{ext_conf}' has not been read.\n{ex}")

        conf.update(extended_config)
        print('Config has been successfully updated!')

    elif os.path.exists(ext_conf) and os.path.getsize(ext_conf) == 0:
        print(f"External config '{ext_conf}' is empty, but it is OK!")
    else:
        raise FileNotFoundError(f"External config '{ext_conf}' has not been found!")

    return conf


def extract_file(files):
    name = date = ''
    regex = r'nginx-access-ui.log-(\d{8})(?:\.gz)?$'
    for current_name in files:
        current_search = re.match(regex, current_name)
        if not current_search:
            continue
        try:
            parse_file_date = datetime.strptime(current_search[1], '%Y%m%d')
        except ValueError:
            continue
        format_file_date = datetime.strftime(parse_file_date, '%Y.%m.%d')
        if format_file_date > date:
            name = current_name
            date = format_file_date
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

    file, file_date = extract_file(files)

    if not file:
        logging.info('No one log file for parsing has been found!')
        return

    Logfile = namedtuple('Logfile', 'name date')
    log_file = Logfile(file, file_date)
    logging.info(f"Required log file '{log_file.name}' has been found.")

    return log_file


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


def prepare_report_url_list(conf, urls_dict, counter_urls, parsed_queries, parsed_queries_time, fails):
    report_urls_list = []
    for key, value in counter_urls.most_common(conf['REPORT_SIZE']):
        report_url = serialize_data(urls_dict, parsed_queries, parsed_queries_time, fails, key, value)
        report_urls_list.append(report_url)
    logging.info('Parsed data have been serialized.')
    return report_urls_list


def parse_string(line):
    decode_line = line.decode('utf-8')
    try:
        url = decode_line.split('HTTP')[0].split()[-1]
        query_time = float(decode_line.rsplit(maxsplit=1)[-1])
    except Exception as ex:
        logging.error(ex)
        return None, None
    return url, query_time


def log_parser(log_file, conf, parse_func):
    urls_dict = {}
    counter_urls = Counter()
    parsed_queries = parsed_queries_time = fails = 0

    operator = gzip.open if log_file.name.endswith('gz') else open
    with operator(os.path.join(conf['LOG_DIR'], log_file.name), 'rb') as file:
        for line in file:
            url, query_time = parse_func(line)
            if not url:
                fails += 1
                continue
            parsed_queries += 1
            parsed_queries_time += query_time
            counter_urls[url] += query_time
            urls_dict.setdefault(url, []).append(query_time)

    if fails * 100 / (parsed_queries + fails) >= conf.get('TOTAL_FAILS', 51):
        raise ValueError('Number of failed operations exceeded the allowed threshold!')
    logging.info('Parsing has been successfully completed.')
    return urls_dict, counter_urls, parsed_queries, parsed_queries_time, fails


def generate_report(parsed_list, report_name, template_name):
    try:
        with open(template_name, 'r', encoding='utf-8') as file:
            read_template = file.read()
    except Exception:
        logging.error('Report template error!')
        raise

    report = read_template.replace('$table_json', str(parsed_list))
    try:
        with open(f'{report_name}.tmp', 'w') as file:
            file.write(report)
    except Exception as ex:
        logging.error(ex)
        raise
    os.rename(f'{report_name}.tmp', report_name)
    logging.info(f"Report '{report_name}' has been successfully dumped.")


def main():
    external_config = get_external_config()
    if not external_config:
        raise ValueError('argument "--config" expected at least one argument!')
    upd_config = update_config(deepcopy(config), external_config)

    set_logging(upd_config)

    last_log = find_last_log(upd_config)

    if not last_log:
        sys.exit('Forced termination!')

    report_path = os.path.join(upd_config['REPORT_DIR'], f'report-{last_log.date}.html')

    if os.path.exists(report_path):
        logging.info(f"Required report '{report_path}' already exists.")
        sys.exit('Forced termination!')
    if not os.path.exists(upd_config['REPORT_DIR']):
        os.makedirs(upd_config['REPORT_DIR'])

    parsed_params = log_parser(last_log, upd_config, parse_string)

    report_url_list = prepare_report_url_list(upd_config, *parsed_params)

    generate_report(report_url_list, report_path, 'report.html')

    logging.info('Script has been completed.')


if __name__ == "__main__":
    try:
        main()
    except:
        logging.exception('Critical error!')
