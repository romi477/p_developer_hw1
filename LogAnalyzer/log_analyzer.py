import os
import re
import gzip
import json
import argparse
import logging
from copy import deepcopy
from datetime import datetime
from statistics import mean, median
from collections import namedtuple, Counter


config = {
    'REPORT_SIZE': 1000,
    'REPORT_DIR': './reports',
    'LOG_DIR': './log',
}


_logger = logging.getLogger('log_analyzer')

_handler = logging.StreamHandler()
_handler.setLevel(logging.INFO)
_format = logging.Formatter('[%(levelname)s] %(message)s')
_handler.setFormatter(_format)

_logger.addHandler(_handler)


def get_external_config():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', nargs='?', default='config.json')
    namespace = parser.parse_args()
    return namespace.config


def check_config_params(conf):
    keys = [
        'REPORT_SIZE',
        'REPORT_DIR',
        'LOG_DIR',
        'LOG_FILE',
        'LOG_LEVEL',
        'TOTAL_FAILS',
        'HTTP_CODE_SERIES',
    ]
    missed_keys = []
    for key in keys:
        if not conf.get(key):
            missed_keys.append(key)
    if missed_keys:
        raise ValueError(f'Config file has missed keys: {", ".join(missed_keys)}.')


def update_config(conf, ext_conf):
    if os.path.exists(ext_conf) and os.path.getsize(ext_conf) > 0:
        try:
            with open(ext_conf, 'r') as f:
                extended_config = json.load(f)
        except Exception as ex:
            raise Exception(f'External config "{ext_conf}" has not been read.\n{ex}')
        conf.update(extended_config)
        _logger.info('Config has been successfully updated!')
    elif os.path.exists(ext_conf) and os.path.getsize(ext_conf) == 0:
        _logger.warning(f'External config "{ext_conf}" is empty.')
    else:
        raise FileNotFoundError(f'External config "{ext_conf}" has not been found!')
    check_config_params(conf)
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
        _logger.error(f'Logs directory "{log_dir}" does not exist!')
        return
    if not files:
        _logger.info(f'Log directory "{log_dir}" is empty!')
        return
    file, file_date = extract_file(files)
    if not file:
        _logger.info('No one log file has been found for parsing!')
        return
    Logfile = namedtuple('Logfile', 'name date')
    log_file = Logfile(file, file_date)
    _logger.info(f'Found log file "{file}"')
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
    _logger.info('Parsed data have been serialized.')
    return report_urls_list


def parse_string(split_line):
    try:
        url = ' - '.join([split_line[4], split_line[5], split_line[-1]])
        query_time = split_line[1]
    except IndexError as ex:
        _logger.error(ex)
        return '', float()
    return url, float(query_time)


def log_parser(conf, log_file, parse_func):
    _logger.info('processing ...')
    urls_dict = {}
    counter_urls = Counter()
    parsed_queries = parsed_queries_time = fails = 0

    operator = gzip.open if log_file.name.endswith('gz') else open
    with operator(os.path.join(conf['LOG_DIR'], log_file.name), 'rb') as file:
        for line in file:
            decode_line = line.decode('utf-8')
            split_line = decode_line.split()
            if len(conf['HTTP_CODE_SERIES']) == 3:
                if split_line[-1] != conf['HTTP_CODE_SERIES']:
                    continue
            elif len(conf['HTTP_CODE_SERIES']) == 1:
                if not split_line[-1].startswith(conf['HTTP_CODE_SERIES']):
                    continue
            else:
                _logger.error('Config has wrong value of "HTTP_CODE_SERIES".')
                break
            url, query_time = parse_func(split_line)
            if not url:
                fails += 1
                continue
            parsed_queries += 1
            parsed_queries_time += query_time
            counter_urls[url] += query_time
            urls_dict.setdefault(url, []).append(query_time)
    if not parsed_queries:
        raise ValueError('No one url had been parsed from log file.')
    if fails * 100 / (parsed_queries + fails) >= conf.get('TOTAL_FAILS', 51):
        raise ValueError('Number of failed operations exceeded the allowed threshold!')
    _logger.info('Parsing has been successfully completed.')
    return urls_dict, counter_urls, parsed_queries, parsed_queries_time, fails


def generate_report(parsed_list, report_name, template_name):
    try:
        with open(template_name, 'r', encoding='utf-8') as file:
            read_template = file.read()
    except Exception:
        _logger.error('Report template open error.')
        raise
    report = read_template.replace('$table_json', str(parsed_list))
    try:
        with open(f'{report_name}.tmp', 'w') as file:
            file.write(report)
    except Exception as ex:
        _logger.error(ex)
        raise
    os.rename(f'{report_name}.tmp', report_name)
    _logger.info(f'Report "{report_name}" has been successfully dumped.')


def main():
    external_config = get_external_config()
    if not external_config:
        raise ValueError('argument "--config" expected at least one argument!')
    _config = update_config(deepcopy(config), external_config)
    
    last_log = find_last_log(_config)
    if not last_log:
        return
    parsed_params = log_parser(_config, last_log, parse_string)
    report_url_list = prepare_report_url_list(_config, *parsed_params)
    
    if not os.path.exists(_config['REPORT_DIR']):
        os.makedirs(_config['REPORT_DIR'])
    report_path = os.path.join(
        _config['REPORT_DIR'],
        f'report-{last_log.date}-{_config["HTTP_CODE_SERIES"]}.html',
    )
    generate_report(report_url_list, report_path, 'report.html')
    

if __name__ == '__main__':
    try:
        main()
        _logger.info('Script ended.')
    except Exception as ex:
        _logger.exception(ex)
