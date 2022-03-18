import os

from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy
from kafka import KafkaProducer

db = SQLAlchemy()

kafka_uri = os.environ.get("KAFKA_URI", "0.0.0.0:9092")
print(f"Starting a KafkaProducer instance with URI {kafka_uri}")
kafka_producer = KafkaProducer(bootstrap_servers=kafka_uri)


def create_app(env=None):
    from app.config import config_by_name
    from app.routes import register_routes

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(env, "test"))
    api = Api(app, title="UdaConnect API", version="0.1.0")

    CORS(app)  # Set CORS for development

    register_routes(api, app)
    db.init_app(app)

    @app.route("/health")
    def health():
        return jsonify("healthy")

    return app
