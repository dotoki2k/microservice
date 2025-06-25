import pika
import json
import time


def callback(ch, method, properties, body):
    print("------------------------------------------------------")
    print(f" [x] Received message from queue 'order_notifications'")

    try:
        order_data = json.loads(body)
        print(f"     Processing order: {order_data}")

        print(
            f"     Sending confirmation email to {order_data.get('user_email')} for order {order_data.get('order_id')}..."
        )
        time.sleep(2)
        print(f" [✔] Email sent successfully.")
        # -----------------------------

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f" [!] Error processing message: {e}")

    print("------------------------------------------------------")


print(" [*] Waiting for messages. To exit press CTRL+C")
connection = pika.BlockingConnection(pika.ConnectionParameters("127.0.0.1"))
channel = connection.channel()

channel.queue_declare(queue="order_notifications", durable=True)

channel.basic_consume(queue="order_notifications", on_message_callback=callback)

channel.start_consuming()
