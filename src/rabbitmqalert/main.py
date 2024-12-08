from __future__ import annotations

import logging
import sys

import click

from . import __version__ as version
from .app import RabbitmqAlertApp
from .config import setup_config
from .logutils import setup_logging
from .notifier import Notifier


@click.command(context_settings={'auto_envvar_prefix': 'RMQ_ALERT'})
@click.version_option(version)
@click.option(
    '--config-file', '-c', 'config_file', default='config.yaml', type=click.Path(),
    help='Path of the configuration file',
)
@click.option(
    '--loglevel', '-l', 'general_loglevel', type=str,
    help='Logging level: DEBUG, INFO, ERROR, CRITICAL, WARNING.',
)
# Telegram
@click.option('--telegram-bot-id', 'telegram_bot_id', help='Telegram bot id to send from.', type=str)
@click.option('--telegram-chat-id', 'telegram_chat_id', help='Telegram channel id to send to.', type=str)
@click.option(
    '--telegram-test', 'telegram_test', is_flag=True, default=False,
    help='Send test messaage to Telegram and exit.',
)
def main(config_file, **cli_options):
    config = setup_config(
        config_file=config_file,
        cli_options=cli_options,
    )
    setup_logging(config)

    logging.info('Starting application...')

    if config['telegram'].get('test'):
        notifier = Notifier(config)
        notifier.send_telegram('Test message.')
        click.echo('Test message to Telegram has been sent.')
        sys.exit(0)

    try:
        app = RabbitmqAlertApp(config=config)
        app.run()
    except KeyboardInterrupt:
        click.echo()
        sys.exit(0)


if __name__ == '__main__':
    main()
