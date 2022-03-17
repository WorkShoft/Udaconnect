from datetime import datetime

from app import db, kafka_producer
from app.udaconnect.models import Location
from app.udaconnect.schemas import (
    LocationSchema, LocationCreateSchema,
)
from app.udaconnect.services import LocationService
from flask import request, json
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource

DATE_FORMAT = "%Y-%m-%d"

api = Namespace("Locations API", description="Connections via geolocation.")  # noqa


# TODO: This needs better exception handling


@api.route("/locations")
@api.route("/locations/<location_id>")
@api.param("location_id", "Unique ID for a given Location", _in="query")
class LocationResource(Resource):
    @accepts(schema=LocationCreateSchema)
    @responds(schema=LocationSchema)
    def post(self) -> Location:
        kafka_producer.send("locations", request.data)

        return request.get_json()

    @responds(schema=LocationSchema)
    def get(self, location_id) -> Location:
        location: Location = LocationService.retrieve(location_id)
        return location


@api.route("/locations/persons/<person_id>")
@api.param("person_id", "Unique ID for a given Person", _in="query")
class LocationResource(Resource):

    @responds(schema=LocationSchema, many=True)
    def get(self, person_id):
        end_date = request.args.get("end_date")
        end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        start_date = request.args.get("start_date")
        start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")

        locations = db.session.query(Location).filter(
            Location.person_id == person_id
        ).filter(Location.creation_time < end_date).filter(
            Location.creation_time >= start_date
        ).all()

        return locations

    @responds(schema=LocationSchema)
    def post(self):
        topic_name = "locations"
        data = api.payload

        kafka_producer.send(topic_name, json.dumps(data))

        return data

        # end_date = request.args.get("end_date")
        # end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        # start_date = request.args.get("start_date")
        # start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        #
        # locations = db.session.query(Location).filter(
        #     Location.person_id == person_id
        # ).filter(Location.creation_time < end_date).filter(
        #     Location.creation_time >= start_date
        # ).all()
        #
        # return locations


