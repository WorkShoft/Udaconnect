import os

import grpc
from app.location_pb2_grpc import LocationServiceStub
from app.location_pb2 import Request

LOCATIONS_PORT = "5001"
LOCATIONS_HOST = "localhost"
GRPC_PORT = os.environ.get("GPRC_PORT", 5005)
GRPC_HOST = os.environ.get("GRPC_HOST", "grpc-server")

channel = grpc.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}", options=(('grpc.enable_http_proxy', 0),))

if os.environ.get('https_proxy'):
    del os.environ['https_proxy']
if os.environ.get('http_proxy'):
    del os.environ['http_proxy']

stub = LocationServiceStub(channel)


class LocationsClient:
    @staticmethod
    def get_location_list(person_id, start_date, end_date):
        """
           Find some Person's location list
        :param person_id:
        :param start_date:
        :param end_date:
        :return:
        """

        request = Request(
            person_id=int(person_id),
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )

        response = stub.Get(request)

        return response.locations
