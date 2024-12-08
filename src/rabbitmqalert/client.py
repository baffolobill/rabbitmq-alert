from __future__ import annotations

import logging
import typing

import requests
from requests.auth import HTTPBasicAuth


class RabbitmqClient:

    def __init__(self, config: dict[str, typing.Any]):
        self.config = config

    @property
    def server_config(self) -> dict[str, typing.Any]:
        return self.config['server']

    def get_queue(self, queue_name: str):
        uri = '/api/queues/{vhost}/{queue}'.format(
            vhost=self.server_config['vhost'],
            queue=queue_name,
        )
        data = self.send_request(uri)

        return data

    def get_queues(self) -> list[str]:
        uri = '/api/queues?page=1&page_size=300'
        data = self.send_request(uri)
        if data is None:
            logging.error('No queues discovered (request failed).')
            return []

        queues = []
        for queue in data.get('items'):
            queues.append(queue.get('name'))

        if queues:
            logging.info('Queues discovered: %s', ', '.join(queues))
        else:
            logging.error('No queues discovered.')

        return queues

    def get_connections(self):
        uri = '/api/connections'
        return self.send_request(uri)

    def get_consumers(self):
        uri = '/api/consumers'
        return self.send_request(uri)

    def get_nodes(self):
        uri = '/api/nodes'
        return self.send_request(uri)

    def send_request(self, uri: str) -> dict | None:
        api_url = '{url}{uri}'.format(
            url=self.server_config['url'],
            uri=uri,
        )

        auth = HTTPBasicAuth(
            self.server_config['username'],
            self.server_config['password'],
        )

        try:
            response = requests.get(api_url, auth=auth, timeout=1)

            return response.json()
        except (requests.ConnectionError) as exp:
            logging.error(f'Error while consuming the API endpoint "{api_url}": {exp}')
            return None
