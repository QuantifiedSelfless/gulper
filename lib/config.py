import configparser

CONFIG = {}


def read_config(mode):
    global CONFIG
    print("Loading config with mode: {}".format(mode))
    config = configparser.ConfigParser()
    config.read('config.conf')
    CONFIG.update(config['default'])
    CONFIG.update(config[mode])
    CONFIG['_mode'] = mode
