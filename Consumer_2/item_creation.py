import pika
import json
import logging

logging.basicConfig(level=logging.DEBUG)

credentials = pika.PlainCredentials(username="guest", password="guest")
parameters = pika.ConnectionParameters(host="rabbitmq", port=5672, credentials=credentials)
connection = pika.BlockingConnection(parameters=parameters)
channel = connection.channel()

channel.queue_declare(queue='insert_item', durable=True)

def callback(ch, method, properties, body):
    body = body.decode()
    body = json.loads(body)

    print(body)
    logging.debug("in consumer2")
    logging.debug("{Item Name: "+body['name']+", Description: "+body['description']+", SKU: "+body['sku']+", Cost_price: "+body['cost_price']+", Selling_price: "+body['selling_price']+", Initial Stock: "+body['initial_stock']+", Reorder: "+body['reorder_point']+"}")

    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue="insert_item", on_message_callback=callback)

print("Waiting for message")
channel.start_consuming()