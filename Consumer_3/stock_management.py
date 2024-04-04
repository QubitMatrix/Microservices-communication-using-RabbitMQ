
import pika
import json
import logging
import pymongo
from bson import ObjectId


logging.basicConfig(level=logging.DEBUG)

credentials = pika.PlainCredentials(username="guest", password="guest")
parameters = pika.ConnectionParameters(host="rabbitmq", port=5672, credentials=credentials)
connection = pika.BlockingConnection(parameters=parameters)
channel = connection.channel()

#channel.exchange_declare(exchange='microservices', exchange_type='direct', durable=True)
channel.queue_declare(queue='stock_manage', durable=True)
channel.queue_declare(queue="process_order", durable=True)


#for reading
#channel.queue_declare(queue='stock_read', durable=True)
#channel.queue_bind(exchange='microservices', queue='read_db', routing_key='read_db')

def manage(ch, method, properties, body):
    body = body.decode()
    body = json.loads(body)
    client = pymongo.MongoClient("mongodb://mongo_db:27017")
    db = client['microservices_db']
    collection = db['item_details']
    sku=body['sku']
    data=list(collection.find({'SKU':sku},{"_id":0}))
    logging.debug("sku:"+sku)
    logging.debug("in consumer3")
    #logging.debug("abc"+"\n".join([str(x) for x in data]))
    mes=json.dumps([{
        str(key): str(value) if isinstance(value, ObjectId) else value
        for key, value in record.items()
    } for record in data])
    logging.debug("check1")
    logging.debug(mes)
    channel.basic_publish(exchange='', routing_key='stock_read', body=mes)
    channel.basic_ack(delivery_tag=method.delivery_tag)

'''channel.queue_declare(queue='read_db', durable=True)
def check(ch,method,properties,body):
    body = body.decode()
    body = json.loads(body)
    logging.debug("check1"+body['Name'])
    logging.debug("check2"+body['Initial Stock'])
    stock_data={'name':body['Name'],'Initial Stock':body['Initial Stock']}
    send_to_stock_display(stock_data)
    ch.basic_ack(delivery_tag=method.delivery_tag)
def send_to_stock_display(data):
  response = requests.post("http://localhost:5000/stock_display", json=data)'''

#channel.basic_consume(queue="read_db", on_message_callback=check)

channel.basic_consume(queue="stock_manage", on_message_callback=manage)

def update_db(ch,method,properties, body):
    body = body.decode()
    body = json.loads(body)
    sku=body['SKU']
    count_neg = body['order_count']
    logging.debug("update:"+count_neg)
    count_neg = -1*int(count_neg)
    channel.basic_ack(delivery_tag=method.delivery_tag)
    client = pymongo.MongoClient("mongodb://mongo_db:27017")
    db = client['microservices_db']
    collection = db['item_details']
    collection.find({'SKU':sku},{"_id":0})
    collection.update_one({'SKU':sku},{"$inc":{'Current Stock':count_neg}})

channel.basic_consume(queue="process_order", on_message_callback=update_db)
print("Waiting for message")
channel.start_consuming()

