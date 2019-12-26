import logging as logger
from flask import current_app, g


def log():
    if 'logger' not in g:
        g.logger = logger
        logging_level = current_app.config['LOG_LEVEL']
        g.logger.basicConfig(level=logging_level, format='%(asctime)s: [%(levelname)s] (%(threadName)-10s) %(message)s',)

    return g.logger
