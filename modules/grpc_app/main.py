import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import grpc
from sqlalchemy import func

from modules.grpc_app import location_pb2
from modules.grpc_app import location_pb2_grpc
from app import db
from app.udaconnect import Location
from modules.grpc_app.location_pb2 import LocationMessage


class LocationServicer(location_pb2_grpc.LocationServiceServicer):
    app = None

    def Create(self, request, context):
        end_date = request.end_date
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = request.start_date
        start_date = datetime.strptime(start_date, "%Y-%m-%d")

        from modules.persons_api.wsgi import app

        location_messages = []

        with app.app_context():
            locations = db.session.query(Location) \
                .with_entities(
                    Location.id,
                    Location.creation_time,
                    func.st_x(Location.coordinate).label("longitude"),
                    func.st_y(Location.coordinate).label("latitude"),
                    Location.person_id) \
                .filter(Location.person_id == request.person_id) \
                .filter(Location.creation_time < end_date) \
                .filter(Location.creation_time >= start_date) \
                .all()

            for row in locations:
                location_messages.append(
                    LocationMessage(
                        id=row.id,
                        creation_time=datetime.strftime(row.creation_time, "%Y-%m-%d"),
                        longitude=row.longitude,
                        latitude=row.latitude,
                        person_id=row.person_id,
                    )
                )

        return location_pb2.LocationMessageList(locations=location_messages)


# Initialize gRPC server

server = grpc.server(ThreadPoolExecutor(max_workers=2))
location_pb2_grpc.add_LocationServiceServicer_to_server(LocationServicer(), server)

PORT = 5005
print(f"Server starting on port {PORT}")
server.add_insecure_port(f"[::]:{PORT}")
server.start()

try:
    while True:
        time.sleep(86400)
except KeyboardInterrupt:
    print("\nGoodbye")
    server.stop(0)
