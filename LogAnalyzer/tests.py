import unittest
from log_analyzer import *


class TestLogAnalyzer(unittest.TestCase):

    def test_update_config_wrong_external_config(self):
        with self.assertRaises(FileNotFoundError): update_config(config, 'wrong_config.json', 'config.json')
        with self.assertRaises(FileNotFoundError): update_config(config, 'wrong_dir/wrong_config.json', 'config.json')

    def test_get_file_date(self):
        files1 = [
            'nginx-access-ui.log-20170320',
            'ngin-acces-ui.log-20220320',
            'ngin-acces-ui-log-20230320',
            'nginx-access-ui.log-20170320.gz',
            'nginx-access-ui.log-20160221.tar.gz',
            'nginx-access-ui.log-20150412',
            'nginx-access-ui.log-20140412',
            'nginx-access-ui.log-20180101',
            'nginx-access-ui.log-20220912.g',
            'nginx-access-ui.log-20080226.tar.gz',
            'nginx-access-ui.log-20190805.gz',
            'nginx-access-ui.log-20190805 ',
            'nginx-access-ui.log-20210226.tar',
        ]
        files2 = [
            'ginx-access-ui.log-20160320',
            'nginx-access-ui.log-2022032',
            'ngin-acces-ui-log-20230320',
            'nginx-access-ui.log-20170320.ta.gz',
            'nginx-access-ui.log-20160221.tar',
        ]
        files3 = []

        self.assertEqual(extract_file(files1), ('nginx-access-ui.log-20190805.gz', '20190805'))
        self.assertIsInstance(extract_file(files1), tuple)
        self.assertIsInstance(extract_file(files2), tuple)
        self.assertIsInstance(extract_file(files3), tuple)
        self.assertEqual(extract_file(files2), ('', ''))
        self.assertEqual(extract_file(files3), ('', ''))

    def test_find_last_log_wrong_logdir(self):
        self.assertIsNone(find_last_log({'LOG_DIR': 'log3'}))
        self.assertIsNone(find_last_log({'LOG_DIR': 'log5'}))

    def test_parse_string_wrong_string(self):
        self.assertEqual(parse_string(b'0x2f6x0x0x02e0e0e34'), (None, None))

    def test_generate_report_wrong_templates(self):
        self.assertIsNone(generate_report(['foo', 'bar'], 'test_report.html', 'wrong_report.html'))
        self.assertIsNone(generate_report(['foo', 'bar'], '', 'report.html'))

if __name__ == '__main__':
    unittest.main()