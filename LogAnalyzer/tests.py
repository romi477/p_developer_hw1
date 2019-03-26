import unittest
from .log_analyzer import *


class TestUpdateConfig(unittest.TestCase):
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
            'notexists_dir/config.json'), tuple)








if __name__ == '__main__':
    unittest.main()