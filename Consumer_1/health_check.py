import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
channel = connection.channel()

channel.queue_declare(queue='health_check')

def callback(ch, method, properties, body):
    print("Health check message received:", body.decode())
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='health_check', on_message_callback=callback, auto_ack=True)

print('Waiting for messages...')
channel.start_consuming()
