import json
import os

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

from app import create_app
from app.udaconnect.services import LocationService


def run_kafka_consumer():
    """
    https://kafka-python.readthedocs.io/en/master/#kafkaconsumer
    :return:
    """

    kafka_uri = os.environ.get("KAFKA_URI", "localhost:9092")  # "kafka-bitnami:9092"
    topic_name = "locations"

    print(f"Connecting to Kafka at {kafka_uri}")

    try:
        app = create_app(os.getenv("FLASK_ENV") or "test")
        with app.app_context():
            consumer = KafkaConsumer(topic_name, bootstrap_servers=kafka_uri)
            for msg in consumer:
                location_dict = json.loads(msg.value)
                LocationService.create(location_dict)
                print(f"Created Location object {location_dict}")

    except NoBrokersAvailable as e:
        print(f"Failed to establish a connection ({e})")


if __name__ == "__main__":
    run_kafka_consumer()
