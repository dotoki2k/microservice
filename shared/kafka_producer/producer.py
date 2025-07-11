# producer.py
import json
import time
from kafka import KafkaProducer

KAFKA_BROKERS = ["localhost:9092"]


def json_serializer(data):
    return json.dumps(data).encode("utf-8")


producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKERS,
    value_serializer=json_serializer,
    client_id="my-producer",
)


def send_message_to_kafka_server(topic_name: str, message: dict):
    """
    Send the message to the topic in the Kafka server.
    Args:
        topic_name: The topic name.
        message: The message data.
    """
    try:
        producer.send(topic_name, value=message)
        producer.flush()
        print(f"Sent the message ({message}) to the kafka server.")
    except Exception as e:
        print(
            f"An error occurred while sending the message to the topic ({topic_name})."
        )
        print(str(e))
