from __future__ import annotations

import logging
import typing

if typing.TYPE_CHECKING:
    from .app import RabbitmqAlertApp
    from .client import RabbitmqClient
    from .notifier import Notifier


class BaseCheckerRule:
    config_section_name: str | None = None

    def __init__(self, checker: Checker):
        self._checker = checker

    @property
    def client(self) -> RabbitmqClient:
        return self._checker._client

    @property
    def config(self) -> dict[str, typing.Any]:
        return self._checker._app.config

    def rules_config(self, key: str, default: typing.Any = None) -> typing.Any:
        return self.config.get('rules', {}).get(key, default)

    def section_config(self, key: str, default: typing.Any = None) -> typing.Any:
        if self.config_section_name is None:
            raise Exception('config_section_name must be defined to use this method')

        return self.rules_config(self.config_section_name, {}).get(key, default)

    def notify(self, message: str):
        self._checker._notifier.send_notification(message=message)

    def check(self, *args, **kwargs: typing.Any):
        raise NotImplementedError('Implement in child class.')

    def run(self):
        raise NotImplementedError('Implement in child class.')


class QueueCheckerRule(BaseCheckerRule):
    config_section_name = 'queue'

    def check(self, queue_name: str, queue_conditions: dict[str, typing.Any]):
        response = self.client.get_queue(queue_name=queue_name)
        if response is None:
            logging.debug(f'No response for "get_queue({queue_name})" request.')
            return
        else:
            logging.debug(f'Response for "get_queue({queue_name})": {response}')

        messages_ready = response.get('messages_ready')
        messages_unacknowledged = response.get('messages_unacknowledged')
        messages = response.get('messages')
        consumers = response.get('consumers')

        ready_size = queue_conditions.get('ready_queue_size')
        unack_size = queue_conditions.get('unack_queue_size')
        total_size = queue_conditions.get('total_queue_size')
        consumers_connected_min = queue_conditions.get('queue_consumers_connected')

        if ready_size is not None and messages_ready > ready_size:
            self.notify(f'Queue[{queue_name}]: messages_ready = {messages_ready} > {ready_size}')

        if unack_size is not None and messages_unacknowledged > unack_size:
            self.notify(f'Queue[{queue_name}]: messages_unacknowledged = {messages_unacknowledged} > {unack_size}')

        if total_size is not None and messages > total_size:
            self.notify(f'Queue[{queue_name}]: messages = {messages} > {total_size}')

        if consumers_connected_min is not None and consumers < consumers_connected_min:
            self.notify(f'Queue[{queue_name}]: consumers_connected = {consumers} < {consumers_connected_min}')

    def run(self) -> None:
        # FIXME: optimization required. This part is called every check.
        server_queues = self.config['server'].get('queues', [])
        if self.config['server'].get('queues_discovery'):
            server_queues = self._discover_upstream_queues()

        if not server_queues:
            logging.info('No queues for checker.')
            return None

        for queue_name in server_queues:
            queue_conditions = self._get_queue_conditions(queue_name=queue_name)

            if (
                queue_conditions['ready_queue_size'] is not None
                or queue_conditions['unack_queue_size'] is not None
                or queue_conditions['total_queue_size'] is not None
                or queue_conditions['queue_consumers_connected'] is not None
            ):
                self.check(
                    queue_name=queue_name,
                    queue_conditions=queue_conditions,
                )

    def _discover_upstream_queues(self) -> list[str] | None:
        response = self.client.get_queues()
        if response is None:
            logging.debug('No response for "get_queues()" request.')
            return
        else:
            logging.debug(f'Response for "get_queues()": {response}')
        return response

    def _get_queue_conditions(self, queue_name: str) -> dict[str, typing.Any]:
        default_conditions = self.section_config('default', {})
        queue_conditions = self.section_config(queue_name, {})
        return {
            **default_conditions,
            **queue_conditions,
        }


class NodeCheckerRule(BaseCheckerRule):
    config_section_name = 'node'

    def check(self):
        response = self.client.get_nodes()
        if response is None:
            logging.debug('No response for "get_nodes()" request.')
            return
        else:
            logging.debug(f'Response for "get_nodes()": {response}')

        nodes_running = len(response)
        nodes_run = self.section_config('nodes_running')
        node_memory_mb = self.section_config('node_memory_used_mb')
        node_memory_bytes = ((node_memory_mb * 1024 ** 2) if node_memory_mb is not None else None)

        if (
            nodes_run is not None
            and nodes_running < nodes_run
        ):
            self.notify(f'nodes_running = {nodes_running} < {nodes_run}')

        for node in response:
            node_name = node.get('name')
            node_mem_used_bytes = node.get('mem_used')
            if (
                node_memory_bytes is not None
                and node_mem_used_bytes is not None
                and node_mem_used_bytes > node_memory_bytes
            ):
                node_mem_used_mb = node_mem_used_bytes / 1024 ** 2
                self.notify(
                    f'Node {node_name} - node_memory_used = {node_mem_used_mb} > {node_memory_mb} (MBs)')

    def run(self):
        if (
            self.section_config('nodes_running') is not None
            or self.section_config('node_memory_used_mb') is not None
        ):
            self.check()


class ConnectionCheckerRule(BaseCheckerRule):
    config_section_name = 'connection'

    def check(self):
        response = self.client.get_connections()
        if response is None:
            logging.debug('No response for "get_connections()" request.')
            return
        else:
            logging.debug(f'Response for "get_connections()": {response}')

        open_connections = len(response)
        open_connections_min = self.section_config('open_connections')

        if open_connections is not None and open_connections < open_connections_min:
            self.notify(f'Total open_connections = {open_connections} < {open_connections_min}')

    def run(self):
        config_value = self.section_config('open_connections')
        if config_value is not None:
            self.check()


class ConsumerCheckerRule(BaseCheckerRule):
    config_section_name = 'consumer'

    def check(self):
        response = self.client.get_consumers()
        if response is None:
            return

        consumers_connected = len(response)
        consumers_connected_min = self.section_config('consumers_connected')

        if (
            consumers_connected is not None
            and consumers_connected < consumers_connected_min
        ):
            self.notify(
                f'Total consumers_connected = {consumers_connected} < {consumers_connected_min}')

    def run(self):
        config_value = self.section_config('consumers_connected')
        if config_value is not None:
            self.check()


class Checker:
    rule_classes = [
        QueueCheckerRule,
        NodeCheckerRule,
        ConnectionCheckerRule,
        ConsumerCheckerRule,
    ]

    def __init__(
        self,
        app: RabbitmqAlertApp,
        client: RabbitmqClient,
        notifier: Notifier,
    ):
        self._app = app
        self._client = client
        self._notifier = notifier

    def get_rules(self) -> list[BaseCheckerRule]:
        rules = [
            rule_class(checker=self)
            for rule_class in self.rule_classes
        ]
        return rules

    def run(self):
        for rule in self.get_rules():
            logging.info(f'Executing rule {rule.__class__.__name__} ...')
            try:
                rule.run()
            except Exception:
                logging.exception(f"Couldn't execute checker rule: {rule.__class__.__name__}")
