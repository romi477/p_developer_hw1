import sys
import os
import json
import logging


config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}


def set_logging(config):
    logging.basicConfig(
        filename=config.get('LOG_FILE'),
        filemode='w',
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S'
    )

def update_config(config):
    config_path = './config.json'
    if sys.argv[1] == '--config':
        try:
            config_path = sys.argv[2]
        except IndexError:
            pass
    else:
        raise ValueError(f"Wrong argument '{sys.argv[1]}'")

    if os.path.exists(config_path) and os.path.getsize(config_path) > 0:

        try:
            with open(config_path, 'r') as f:
                external_config = json.load(f)
        except json.decoder.JSONDecodeError:
            return
        else:
            config.update(external_config)
            return True
    elif os.path.exists(config_path) and os.path.getsize(config_path) == 0:
        return True



def main():
    if len(sys.argv) > 1:
        if not update_config(config):
            sys.exit('External config error! File not found or not parsed!')

    set_logging(config)

    logging.info('HI')
    logging.info(config)


if __name__ == "__main__":
    main()

