# Import necessary libraries
import pika
import json
import logging
import pymongo
from bson import ObjectId

# Display debug info
logging.basicConfig(level=logging.DEBUG)

# RabbitMQ setup
credentials = pika.PlainCredentials(username='guest', password='guest')
parameters = pika.ConnectionParameters(host='rabbitmq', port=5672, credentials=credentials)
connection = pika.BlockingConnection(parameters=parameters)
channel = connection.channel()

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://mongo_db:27017")
db = client["microservices_db"]
collection = db["item_details"]

# Declare the "read_database" queue
channel.queue_declare(queue='read_database', durable=True)

# Define the callback function to process incoming messages
def callback(ch, method, properties, body):
    # Retrieve all records from the database
    records = list(collection.find())
    
    # Serialize records to JSON
    records_json = json.dumps([{
        str(key): str(value) if isinstance(value, ObjectId) else value
        for key, value in record.items()
    } for record in records])
    
    # Log the serialized records
    logging.debug("Serialized records sent to RabbitMQ:")
    logging.debug(records_json)
    
    # Send records to the send_database queue
    channel.basic_publish(exchange='', routing_key='send_database', body=records_json)

    # Acknowledge that the message has been processed
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Consume messages from the "read_database" queue
channel.basic_consume(queue='read_database', on_message_callback=callback)

# Start consuming messages
print('Waiting for messages...')
channel.start_consuming()

