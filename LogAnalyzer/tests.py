import unittest
import gzip, bz2
from log_analyzer import *


class TestLogAnalyzer(unittest.TestCase):

    def test_get_file_date(self):
        files1 = [
            'nginx-access-ui.log-20160320',
            'ngin-acces-ui.log-20220320',
            'ngin-acces-ui-log-20230320',
            'nginx-access-ui.log-20170320.tar.bz2',
            'nginx-access-ui.log-20160221.tar.gz',
            'nginx-access-ui.log-20150412',
            'nginx-access-ui.log-20140412',
            'nginx-access-ui.log-20180101.tar.gz',
            'nginx-access-ui.log-20220912.tar.g',
            'nginx-access-ui.log-20080226.tar.bz2',
            'nginx-access-ui.log-20190805.tar.bz2',
            'nginx-access-ui.log-20210226.tar',
        ]
        files2 = [
            'ginx-access-ui.log-20160320',
            'nginx-access-ui.log-2022032',
            'ngin-acces-ui-log-20230320',
            'nginx-access-ui.log-20170320.ta.bz2',
            'nginx-access-ui.log-20160221.tar',
        ]
        files3 = []

        self.assertEqual(get_file_date(files1), ('nginx-access-ui.log-20190805.tar.bz2', '20190805'))
        self.assertIsInstance(get_file_date(files1), tuple)
        self.assertIsInstance(get_file_date(files2), tuple)
        self.assertIsInstance(get_file_date(files3), tuple)
        self.assertEqual(get_file_date(files2), ('', ''))
        self.assertEqual(get_file_date(files3), ('', ''))









    # def test_update_config_returns_tuple(self):
    #     self.assertIsInstance(update_config(config, 'config.json'), tuple)
    #     self.assertIsInstance(update_config(config, 'config.txt'), tuple)
    #     self.assertIsInstance(update_config(config, 'notexists_config.json'), tuple)
    #     self.assertIsInstance(update_config(config, 'notexists_dir/config.json'), tuple)
    #     self.assertIsInstance(update_config(
    #         {
    #             "error1": 1000,
    #             "error2": "./reports",
    #             "error3": "./log",
    #             "error4": "./logfile.log",
    #             "error5": "DEBUG",
    #             "error6": 51
    #         },
    #     'notexists_dir/config.json'
    #     ), tuple)
    #
    # def test_find_last_log_returns_tuple(self):
    #     self.assertIsInstance(find_last_log(config), tuple)
    #     self.assertIsInstance(find_last_log(
    #         {
    #             "error1": 1000,
    #             "error2": "./reports",
    #             "LOG_DIR": "./log",
    #             "error4": "./logfile.log",
    #             "error5": "DEBUG",
    #             "error6": 51
    #         }
    #     ), tuple)
    #
    # def test_log_parser_returns_tuple(self):
    #     Logfile = namedtuple('Logfile', 'name date operator')
    #     log = Logfile('nginx-access-ui.log-20160320', '2016.03.20', open)
    #     self.assertIsInstance(log_parser(log, config), tuple)
    #
    # def test_generate_report_returns_tuple(self):
    #     self.assertIsInstance(generate_report({}, 'myreport.html', 'report.html'), tuple)
    #     self.assertIsInstance(generate_report({}, 'myreport.html', 'notexists_report.html'), tuple)
    #     self.assertIsInstance(generate_report({}, 'myreport.html', 'dir/report.html'), tuple)


if __name__ == '__main__':
    unittest.main()