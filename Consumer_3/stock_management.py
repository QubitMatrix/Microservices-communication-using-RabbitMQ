
import pika
import json
import logging

logging.basicConfig(level=logging.DEBUG)

credentials = pika.PlainCredentials(username="guest", password="guest")
parameters = pika.ConnectionParameters(host="rabbitmq", port=5672, credentials=credentials)
connection = pika.BlockingConnection(parameters=parameters)
channel = connection.channel()

channel.queue_declare(queue='stock_manage', durable=True)

def manage(ch, method, properties, body):
    body = body.decode()
    body = json.loads(body)
    logging.debug("in consumer3")
    logging.debug("Item name: "+body['name']+", SKU: "+body['sku']+", Used stock: "+body['used_stock'])
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue="stock_manage", on_message_callback=manage)
print("Waiting for message")
channel.start_consuming()