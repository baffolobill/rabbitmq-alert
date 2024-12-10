from __future__ import annotations

import logging
import time
import typing

from .checker import Checker
from .client import RabbitmqClient
from .notifier import Notifier


class RabbitmqAlertApp:
    def __init__(self, config: dict[str, typing.Any]):
        self.config = config
        self._client = RabbitmqClient(config)
        self._notifier = Notifier(config)
        self._checker = Checker(
            app=self,
            client=self._client,
            notifier=self._notifier,
        )

    def run(self):
        logging.info('Application is starting.')

        check_interval = self.config['general']['check_rate']
        try:
            while True:
                logging.info('Run checkers ...')
                self._checker.run()

                logging.info(f'Wait {check_interval} seconds before next run.')
                time.sleep(check_interval)
        finally:
            pass

        logging.info('Application has been finished.')
