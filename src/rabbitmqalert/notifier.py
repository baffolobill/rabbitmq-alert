from __future__ import annotations

import logging
import typing

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class RetryHTTPAdapter(HTTPAdapter):
    def __init__(self, **kwargs):
        kwargs['max_retries'] = Retry(
            total=10,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=['HEAD', 'GET', 'OPTIONS', 'PATCH', 'PUT', 'POST'],
        )

        super().__init__(**kwargs)


class TelegramNotifier:
    """
    Инструкция по получению Telegram Chat ID:
    - Добавляем бота в нужный канал/чат.
    - Пишем сообщение в чате, используя @mentaion: "test @yourbotname".
    - Вызываем команду `curl https://api.telegram.org/bot<YourBOTToken>/getUpdates`.
    """

    api_url = 'https://api.telegram.org'

    def __init__(
        self, 
        bot_token: str, 
        chat_id: str, 
        notifier: Notifier,
        chat_thread_id: str | None = None,
    ):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.chat_thread_id = chat_thread_id
        self._notifier = notifier

    def is_enabled(self) -> bool:
        if not self._notifier.config['telegram'].get('enabled', False):
            return False

        if not (
            self.bot_token
            and self.chat_id
        ):
            return False
        return True

    def send_message(self, message: str):
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True,
            'disable_notifications': True,
        }
        if self.chat_thread_id is not None:
            data['message_thread_id'] = self.chat_thread_id
        
        try:
            self._make_api_call(
                'post',
                'sendMessage',
                json=data,
                timeout=3,
            )
        except requests.exceptions.Timeout:
            logging.exception("Couldn't send message to Telegram.")

    def _make_api_call(self, method_name: str, url: str, **kwargs) -> requests.Response | None:
        if not self.is_enabled():
            return None

        kwargs['timeout'] = 3

        if not url.startswith('https://'):
            url = f'{self.api_url}/bot{self.bot_token}/{url}'

        # Request preparation
        http = requests.Session()
        http.mount('https://', RetryHTTPAdapter())

        return getattr(http, method_name.lower())(url, **kwargs)


class Notifier:

    def __init__(self, config: dict[str, typing.Any]):
        self.config = config
        self.telegram_notifier = TelegramNotifier(
            bot_token=self.config['telegram'].get('bot_id'),
            chat_id=self.config['telegram'].get('chat_id'),
            chat_thread_id=self.config['telegram'].get('chat_thread_id'),
            notifier=self,
        )

    def send_notification(self, message: str):
        text = f"{self.config['server']['name']} - {message}"

        logging.info(f'Notify about: {message}')

        if self.telegram_notifier.is_enabled():
            self.send_telegram(message=text)

    def send_telegram(self, message: str):
        logging.info(f'Sending Telegram notification: {message}')

        self.telegram_notifier.send_message(message=message)
