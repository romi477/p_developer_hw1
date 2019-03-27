import unittest
import gzip, bz2
from log_analyzer import *


class TestLogAnalyzer(unittest.TestCase):

    def test_update_config_returns_tuple(self):
        self.assertIsInstance(update_config(config, 'config.json'), tuple)
        self.assertIsInstance(update_config(config, 'config.txt'), tuple)
        self.assertIsInstance(update_config(config, 'notexists_config.json'), tuple)
        self.assertIsInstance(update_config(config, 'notexists_dir/config.json'), tuple)
        self.assertIsInstance(update_config(
            {
                "error1": 1000,
                "error2": "./reports",
                "error3": "./log",
                "error4": "./logfile.log",
                "error5": "DEBUG",
                "error6": 51
            },
        'notexists_dir/config.json'
        ), tuple)

    def test_find_last_log_returns_tuple(self):
        self.assertIsInstance(find_last_log(config), tuple)
        self.assertIsInstance(find_last_log(
            {
                "error1": 1000,
                "error2": "./reports",
                "LOG_DIR": "./log",
                "error4": "./logfile.log",
                "error5": "DEBUG",
                "error6": 51
            }
        ), tuple)

    def test_log_parser_returns_tuple(self):
        Logfile = namedtuple('Logfile', 'name date operator')
        log = Logfile('nginx-access-ui.log-20160320', '2016.03.20', open)
        self.assertIsInstance(log_parser(log, config), tuple)

    def test_generate_report_returns_tuple(self):
        self.assertIsInstance(generate_report({}, 'myreport.html', 'report.html'), tuple)
        self.assertIsInstance(generate_report({}, 'myreport.html', 'notexists_report.html'), tuple)
        self.assertIsInstance(generate_report({}, 'myreport.html', 'dir/report.html'), tuple)


if __name__ == '__main__':
    unittest.main()