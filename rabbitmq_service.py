import pika
class RabbitMQService:
    def __init__(self):
        self.connection = None
        self.channel = None

    def connect(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()

    def close(self):
        if self.channel:
            self.channel.close()
        if self.connection:
            self.connection.close()

    def receive_message(self, queue, callback):
        self.channel.queue_declare(queue=queue, durable=False)
        self.channel.basic_consume(
            queue=queue, on_message_callback=callback, auto_ack=True)
        print(f'[*] Waiting for messages in {queue}')
        self.channel.start_consuming()

    def send_message(self, queue, message):
        self.channel.queue_declare(queue=queue, durable=True)
        self.channel.basic_publish(
            exchange='', routing_key=queue, body=message)
        print(f"[x] Sent {message} to queue '{queue}'")

