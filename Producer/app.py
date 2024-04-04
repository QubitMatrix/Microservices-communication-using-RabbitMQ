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

#insert_item
channel.queue_declare(queue="insert_item", durable=True)
channel.queue_bind(exchange='microservices', queue='insert_item', routing_key='insert_item')

#stock_management
#channel.queue_declare(queue="stock_manage", durable=True)
#channel.queue_bind(exchange='microservices', queue='stock_manage', routing_key='stock_manage')

channel.queue_declare(queue='stock_read', durable=True)
channel.queue_declare(queue="stock_manage", durable=True)
channel.queue_bind(exchange='microservices', queue='stock_manage', routing_key='stock_manage')

@app.route('/')
def index():
    return render_template("index.html")

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    # Check RabbitMQ health
    rabbitmq_status = check_rabbitmq_health()

    # Determine overall health status
    if rabbitmq_status['status'] == 'ok':
        overall_status = 'ok'
    else:
        overall_status = 'error'

    return jsonify({'status': overall_status})

# Function to check RabbitMQ health
def check_rabbitmq_health():
    try:
        # Establish connection to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
        connection.close()
        return {'status': 'ok', 'details': 'RabbitMQ connection successful'}
    except Exception as e:
        return {'status': 'error', 'details': str(e)}

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
@app.route('/order_processing', methods=['GET'])
def order_processing():
    return render_template("read.html")
    # return jsonify({'status': 'success', 'message': 'Order processed successfully'})

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