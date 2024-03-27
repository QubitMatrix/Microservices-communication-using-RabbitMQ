import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
channel = connection.channel()

channel.queue_declare(queue='order_processing')

def callback(ch, method, properties, body):
    print("Order processing message received:", body.decode())

channel.basic_consume(queue='order_processing', on_message_callback=callback, auto_ack=True)

print('Waiting for messages...')
channel.start_consuming()
