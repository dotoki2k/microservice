import pika
import json


def send_message_to_rabitmq_sever(message: dict, queue_key: str):
    """Send the message to the RabitMQ server.

    Args:
        message: The message context.
        queue_key: The queue key in the RabitMQ.
    """
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters("127.0.0.1"))
        channel = connection.channel()
        channel.queue_declare(queue=queue_key, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=queue_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ),
        )
        connection.close()
        print(f" [v] Sent message to the sever")
    except Exception as e:
        print(f" [!] Failed to send message to RabbitMQ: {e}")
