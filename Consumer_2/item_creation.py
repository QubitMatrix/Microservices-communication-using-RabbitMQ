import pika
import json
import logging
import pymongo

# Display debug info
logging.basicConfig(level=logging.DEBUG)

# Setup rabbitmq 
credentials = pika.PlainCredentials(username="guest", password="guest")
parameters = pika.ConnectionParameters(host="rabbitmq", port=5672, credentials=credentials)
connection = pika.BlockingConnection(parameters=parameters)
channel = connection.channel()

# declare insert_item queue
channel.queue_declare(queue='insert_item', durable=True)

# callback when read from queue
def callback(ch, method, properties, body):
    body = body.decode()
    body = json.loads(body)

    name = body['name']
    desc = body['description']
    sku = body['sku']
    cost_price = body['cost_price']
    selling_price = body['selling_price']
    initial_stock = body['initial_stock']
    reorder = body['reorder_point']
    cur_stock=int(initial_stock)

    logging.debug("in consumer2")
    logging.debug("{Item Name: "+name+", Description: "+desc+", SKU: "+sku+", Cost_price: "+cost_price+", Selling_price: "+selling_price+", Initial Stock: "+initial_stock+", Reorder: "+reorder+", Current Stock: "+initial_stock+"}")
    
    client = pymongo.MongoClient("mongodb://mongo_db:27017")
    db = client['microservices_db']
    collection = db['item_details']
    record = {"Name": name, "Description": desc, "SKU": sku, "Cost Price": cost_price, "Selling Price": selling_price, "Initial Stock": initial_stock, "Reorder Point": reorder, "Current Stock": cur_stock}
    logging.debug("Before mongo insert")
    collection.insert_one(record)
    logging.debug("After mongo insert")
    logging.debug("abc"+"\n".join([ str(x) for x in collection.find()]))
    client.close()

    ch.basic_ack(delivery_tag=method.delivery_tag)

# config consume from insert_item queue to call callback
channel.basic_consume(queue="insert_item", on_message_callback=callback)

print("Waiting for message")
channel.start_consuming() # start consuming from the queue - infinite blocking connection