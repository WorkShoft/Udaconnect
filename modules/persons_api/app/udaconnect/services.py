import logging
from datetime import datetime, timedelta
from typing import Dict, List

import sqlalchemy
from sqlalchemy import func, and_

from app import db
from app.udaconnect.locations_client import LocationsClient
from app.udaconnect.models import Connection, Location, Person
from app.udaconnect.schemas import ConnectionSchema, LocationSchema, PersonSchema
from geoalchemy2.functions import ST_AsText, ST_Point
from sqlalchemy.sql import text

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("udaconnect-persons_api")


class ConnectionService:
    @staticmethod
    def find_contacts(person_id: int, start_date: datetime, end_date: datetime, meters=5
    ) -> List[Connection]:
        """
        Finds all Person who have been within a given distance of a given Person within a date range.

        This will run rather quickly locally, but this is an expensive method and will take a bit of time to run on
        large datasets. This is by design: what are some ways or techniques to help make this data integrate more
        smoothly for a better user experience for API consumers?

        TODO: pagination
        """

        locations_client = LocationsClient()
        locations: List = locations_client.get_location_list(person_id, start_date, end_date)

        # Cache all users in memory for quick lookup
        person_map: Dict[str, Person] = {person.id: person for person in PersonService.retrieve_all()}

        result: List[Connection] = []

        for loc in locations:
            loc["start_date"] = start_date.strftime("%Y-%m-%d")
            loc["end_date"] = (end_date + timedelta(days=1)).strftime("%Y-%m-%d")

            query = db.session.query(Location) \
                .with_entities(Location.coordinate, Location.id, Location.person_id, func.st_x(Location.coordinate).label("latitude"), func.st_y(Location.coordinate).label("longitude"), Location.creation_time) \
                .filter(and_(
                    func.ST_DWithin(
                        sqlalchemy.sql.text(
                            f"coordinate::geography,ST_SetSRID(ST_MakePoint({loc.get('latitude')},{loc.get('longitude')}),4326)::geography, {meters}")
                    ),
                    Location.person_id != loc.get("person_id"),
                    datetime.strptime(loc.get("start_date"), '%Y-%m-%d') <= Location.creation_time,
                    datetime.strptime(loc.get("end_date"), '%Y-%m-%d') > Location.creation_time
                )
            ) \
                .first()

            location_object = Location(
                    id=query.id,
                    person_id=query.person_id,
                    creation_time=query.creation_time,
                    coordinate=query.coordinate
                )

            location_object.set_wkt_with_coords(query.latitude, query.longitude)

            result.append(
                Connection(
                    person=person_map.get(location_object.person_id), location=location_object,
                )
            )

        return result


class LocationService:
    @staticmethod
    def retrieve(location_id) -> Location:
        location, coord_text = (
            db.session.query(Location, Location.coordinate.ST_AsText())
            .filter(Location.id == location_id)
            .one()
        )

        # Rely on database to return text form of point to reduce overhead of conversion in app code
        location.wkt_shape = coord_text
        return location

    @staticmethod
    def create(location: Dict) -> Location:
        validation_results: Dict = LocationSchema().validate(location)
        if validation_results:
            logger.warning(f"Unexpected data format in payload: {validation_results}")
            raise Exception(f"Invalid payload: {validation_results}")

        new_location = Location()
        new_location.person_id = location["person_id"]
        new_location.creation_time = location["creation_time"]
        new_location.coordinate = ST_Point(location["latitude"], location["longitude"])
        db.session.add(new_location)
        db.session.commit()

        return new_location


class PersonService:
    @staticmethod
    def create(person: Dict) -> Person:
        new_person = Person()
        new_person.first_name = person["first_name"]
        new_person.last_name = person["last_name"]
        new_person.company_name = person["company_name"]

        db.session.add(new_person)
        db.session.commit()

        return new_person

    @staticmethod
    def retrieve(person_id: int) -> Person:
        person = db.session.query(Person).get(person_id)
        return person

    @staticmethod
    def retrieve_all() -> List[Person]:
        return db.session.query(Person).all()
