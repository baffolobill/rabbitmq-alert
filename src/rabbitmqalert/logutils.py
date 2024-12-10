from __future__ import annotations

import logging

# import os
import sys
import typing

# from logging import handlers

# LOGGING_PATH = '/var/log/rabbitmq-alert/rabbitmq-alert.log'


# class Logger:

#     def __init__(self):
#         self.logger = logging.getLogger()
#         self.logger.setLevel(logging.DEBUG)

#         self._create_logs_dir()
#         rotate_handler = handlers.TimedRotatingFileHandler(
#             filename=LOGGING_PATH,
#             when='midnight',
#         )
#         rotate_handler.suffix = '%Y%m%d'
#         rotate_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
#         self.logger.addHandler(rotate_handler)

#         stoud_handler = logging.StreamHandler(sys.stdout)
#         stoud_handler.setFormatter(logging.Formatter('%(asctime)s: %(levelname)s - %(message)s'))
#         self.logger.addHandler(stoud_handler)

#     def get_logger(self):
#         return self.logger

#     def _create_logs_dir(self):
#         os.makedirs(
#             name=os.path.dirname(LOGGING_PATH),
#             exist_ok=True,
#         )


def setup_logging(config: dict[str, typing.Any]):
    logging.basicConfig(
        format=config['general']['log_format'],
        level=getattr(logging, config['general']['loglevel'].upper()),
        stream=sys.stdout,
    )
