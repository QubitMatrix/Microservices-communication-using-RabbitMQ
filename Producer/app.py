import json
import logging
from flask import Flask, request, render_template
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
channel.queue_declare(queue="insert_item", durable=True)
channel.queue_bind(exchange='microservices', queue='insert_item', routing_key='insert_item')

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/insert_item', methods=['GET'])
def insert_item():
    return render_template("insert.html", message='Insert form rendered')

@app.route('/insert_item_details', methods=['POST'])
def insert_item_details():
    name=request.form['name']
    description=request.form['description']
    sku=request.form['sku']
    cost_price=request.form['cost_price']
    selling_price=request.form['selling_price']
    initial_stock=request.form['initial_stock']
    reorder_point=request.form['reorder_point']

    print(name,description, sku, cost_price, selling_price, initial_stock, reorder_point)
    message = json.dumps({'name': name, 'description': description, 'sku': sku, 'cost_price': cost_price, 'selling_price': selling_price, 'initial_stock': initial_stock, 'reorder_point': reorder_point})
    print(message)
    logging.debug("check1")
    logging.info(message)
    
    channel.basic_publish(exchange='microservices', routing_key='insert_item', body=message)

    return render_template("insert.html", message="Item inserted successfully")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)