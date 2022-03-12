import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import grpc
from dateutil.parser import parse

from grpc_server import location_pb2
from grpc_server import location_pb2_grpc
from grpc_server.location_pb2 import LocationMessage

from app import db
from app.udaconnect import Location

from wsgi import app


class LocationServicer(location_pb2_grpc.LocationServiceServicer):
    def Get(self, request, context):
        end_date = request.end_date

        if is_date(end_date):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        start_date = request.start_date

        if is_date(start_date):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")

        locations = self._get_location_messages(request, start_date=start_date, end_date=end_date)

        return location_pb2.LocationMessageList(locations=locations)

    @staticmethod
    def _get_location_messages(request, start_date=None, end_date=None):
        location_messages = []

        with app.app_context():
            locations = db.session.query(Location).filter(Location.person_id == request.person_id)

            if isinstance(end_date, datetime):
                locations = locations.filter(Location.creation_time < end_date)

            if isinstance(start_date, datetime):
                locations = locations.filter(Location.creation_time >= start_date)

            locations = locations.all()

            for row in locations:
                location_messages.append(
                    LocationMessage(
                        id=row.id,
                        creation_time=datetime.strftime(row.creation_time, "%Y-%m-%d"),
                        longitude=float(row.longitude),
                        latitude=float(row.latitude),
                        person_id=row.person_id,
                    )
                )

        return location_messages


def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True

    https://stackoverflow.com/questions/25341945/check-if-string-has-date-any-format
    """
    try:
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False


def start_server():
    if os.environ.get('https_proxy'):
        del os.environ['https_proxy']
    if os.environ.get('http_proxy'):
        del os.environ['http_proxy']

    port = 5005
    print(f"Server starting on port {port}")
    server = grpc.server(ThreadPoolExecutor(max_workers=2))
    server.add_insecure_port(f"0.0.0.0:{port}")
    server.start()

    return server


# Initialize gRPC server

server_instance = start_server()
location_servicer = LocationServicer()
location_pb2_grpc.add_LocationServiceServicer_to_server(location_servicer, server_instance)

try:
    while True:
        time.sleep(86400)
except KeyboardInterrupt:
    print("\nGoodbye")
    server_instance.stop(0)
