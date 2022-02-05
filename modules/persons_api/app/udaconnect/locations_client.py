import grpc

LOCATIONS_PORT = "5001"
LOCATIONS_HOST = "localhost"
GRPC_PORT = 5005
channel = grpc.insecure_channel(f"localhost:{GRPC_PORT}")

from grpc_server import location_pb2_grpc
from grpc_server import location_pb2

stub = location_pb2_grpc.LocationServiceStub(channel)


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

        request = location_pb2.Request(
            person_id=int(person_id),
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )

        response = stub.Get(request)

        return response.locations
