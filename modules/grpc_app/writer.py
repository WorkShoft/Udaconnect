import grpc

import location_pb2_grpc
import location_pb2

print("Sending sample request")

PORT = 5005
channel = grpc.insecure_channel(f"localhost:{PORT}")
stub = location_pb2_grpc.LocationServiceStub(channel)

location = location_pb2.LocationMessage(
    id=1,
    creation_time="2020-01-01",
    longitude=20.5,
    latitude=59.3,
    person_id=5,
)

request = location_pb2.Request(
    person_id=1,
    start_date="2020-03-06",
    end_date="2022-01-01",
)

response = stub.Create(request)

for loc in response.locations:
    print(loc)
