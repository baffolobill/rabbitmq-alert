# Development

## RabbitMQ

Some helpful commands to add queue and push message to it:
```
rabbitmqadmin declare queue --vhost=primary name=test_queue durable=true
rabbitmqadmin declare exchange --vhost=primary name=test_exchange type=direct
rabbitmqadmin --vhost=primary declare binding source="test_exchange" destination_type="queue" destination="test_queue" routing_key="test"
rabbitmqadmin -V primary publish exchange=test_exchange routing_key=test payload="hello, world"
```