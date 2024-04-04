import json
import logging
from flask import Flask, request, render_template, jsonify
import pika

app = Flask(
    __name__,
    template_folder="templates"
)

logging.basicConfig(level=logging.DEBUG)

credentials = pika.PlainCredentials(username="guest", password="guest")
parameters = pika.ConnectionParameters(host="rabbitmq", port=5672, credentials=credentials)
connection = pika.BlockingConnection(parameters=parameters)
channel = connection.channel()


channel.exchange_declare(exchange='microservices', exchange_type='direct', durable=True)


# health check
channel.queue_declare(queue='health_check', durable=True)
channel.queue_bind(exchange='microservices', queue='health_check', routing_key='health_check')

#insert_item
channel.queue_declare(queue="insert_item", durable=True)
channel.queue_bind(exchange='microservices', queue='insert_item', routing_key='insert_item')

#stock_management
#channel.queue_declare(queue="stock_manage", durable=True)
#channel.queue_bind(exchange='microservices', queue='stock_manage', routing_key='stock_manage')

channel.queue_declare(queue='stock_read', durable=True)
channel.queue_declare(queue="stock_manage", durable=True)
channel.queue_bind(exchange='microservices', queue='stock_manage', routing_key='stock_manage')

#order_processing
channel.queue_declare(queue='send_database', durable=True)
channel.queue_declare(queue="read_database", durable=True)
channel.queue_bind(exchange='microservices', queue='read_database', routing_key='read_database')
channel.queue_declare(queue="process_order", durable=True)
channel.queue_bind(exchange='microservices', queue='process_order', routing_key='process_order')


@app.route('/')
def index():
    return render_template("index.html")

# Health check endpoint
@app.route('/health_check', methods=['GET'])
def health_check():
    message = 'RabbitMQ connection established successfully'
    # Publish message to health_check queue
    channel.basic_publish(exchange='microservices', routing_key='health_check', body=message)
    return 'Health Check message sent!'

# End-point to fill form for create new item
@app.route('/insert_item', methods=['GET'])
def insert_item():
    return render_template("insert.html", message='Insert form rendered')

# End-point to access form data and process it
@app.route('/insert_item_details', methods=['POST'])
def insert_item_details():
    name=request.form['name']
    description=request.form['description']
    sku=request.form['sku']
    cost_price=request.form['cost_price']
    selling_price=request.form['selling_price']
    initial_stock=request.form['initial_stock']
    reorder_point=request.form['reorder_point']

    message = json.dumps({'name': name, 'description': description, 'sku': sku, 'cost_price': cost_price, 'selling_price': selling_price, 'initial_stock': initial_stock, 'reorder_point': reorder_point})
    logging.debug("check1")
    logging.info(message)
    
    channel.basic_publish(exchange='microservices', routing_key='insert_item', body=message) # publish item details to insert_item queue

    return render_template("insert.html", message="Item inserted successfully")

# Endpoint for order processing
@app.route('/read_database', methods=['GET', 'POST'])
def read_database():
    # Receive order details and publish to process_order queue
    logging.debug("req"+request.method)
    if(request.method=='POST'):
        logging.debug("req"+request.method)
        sku=request.form['sku']
        count=request.form['order_count']
        message = json.dumps({'SKU':sku, "order_count":count})
        logging.debug("sku:"+sku)
        logging.debug("count:"+count)
        channel.basic_publish(exchange='microservices', routing_key='process_order', body=message)
        return render_template("index.html")
    # Publish message to read_database queue
    else:
        channel.basic_publish(exchange='microservices', routing_key='read_database', body='Read database request')
        return render_template('read.html', message='Read Database message sent!')

@app.route('/read_database_actually', methods=['GET'])
def read_database_actually():
    # Fetch records from RabbitMQ (send_database queue)
    method_frame, header_frame, body = channel.basic_get(queue='send_database')
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    # Deserialize JSON data
    records = json.loads(body.decode())

    # Return the records as JSON response
    return jsonify(records)

@app.route('/stock_management',methods=['GET','POST'])
def stock_management():
    if request.method =='POST':
        sku=request.form['sku']
        logging.debug("In stock_management_details")
        logging.debug("hijk:"+sku)
        message=json.dumps({'sku':sku})

        channel.basic_publish(exchange='microservices', routing_key='stock_manage', body=message)
        return render_template("stock_manage.html")
        
    return render_template("stock_manage.html")


'''@app.route('/stock_management_details',methods=['POST'])
def stock_management_details():
    sku=request.form['sku']
    logging.debug("In stock_management_details")
    logging.debug(sku)
    message=json.dumps({'sku':sku})

    channel.basic_publish(exchange='microservices', routing_key='stock_manage', body=message)
    return render_template("stock_manage.html")'''

'''def check(ch,method,properties,body):
    body = body.decode()
    body = json.loads(body)
    logging.debug("check1"+body['name'])
    logging.debug("check2"+body['class'])
    ch.basic_ack(delivery_tag=method.delivery_tag)'''
@app.route('/stock_display',methods=['GET'])
def stock_display():
    method_frame, header_frame, body = channel.basic_get(queue='stock_read')
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)
    records = json.loads(body.decode())
    logging.debug("check3")
    return jsonify(records)
    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
