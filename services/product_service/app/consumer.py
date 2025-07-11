import json
import threading
from kafka import KafkaConsumer
from .query import update_stock_quantity
from .database import create_db_session

KAFKA_BROKERS = ["localhost:9092"]
PRODUCT_TOPIC = "product_topic"
CONSUMER_GROUP_ID = "group_consumer_product"
NUM_CONSUMERS = 2


def run_kafka_consumer(consumer_id: str, stop_event: threading.Event):
    consumer = KafkaConsumer(
        PRODUCT_TOPIC,
        bootstrap_servers=KAFKA_BROKERS,
        group_id=CONSUMER_GROUP_ID,
        client_id=consumer_id,
        auto_offset_reset="earliest",
        consumer_timeout_ms=1000,
    )
    db = create_db_session()
    print(f"🚀 [{consumer_id}] Đã sẵn sàng xử lý message...")

    while not stop_event.is_set():
        for partition, messages in consumer.poll(timeout_ms=500).items():
            for message in messages:
                try:
                    data = json.loads(message.value.decode("utf-8"))
                    print(f"Handling the message ({message})")
                    db_product = update_stock_quantity(db, data)
                    if db_product:
                        print(f"Handle the message ({message}) successfully.")
                except Exception as ex:
                    print(f"An error occurred while handling the message ({message})")
                    print(str(ex))

    consumer.close()
    db.close()
    print(f"Consumer[{consumer_id}] closed.")
