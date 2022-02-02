import logging
from datetime import datetime, timedelta
from typing import Dict, List

import sqlalchemy
from sqlalchemy import func, and_, or_

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
    def find_contacts(person_id: int, start_date: datetime, end_date: datetime, page=1, meters=5
                      ) -> List[Connection]:
        """
        Finds all Person who have been within a given distance of a given Person within a date range.

        This will run rather quickly locally, but this is an expensive method and will take a bit of time to run on
        large datasets. This is by design: what are some ways or techniques to help make this data integrate more
        smoothly for a better user experience for API consumers?

        TODO: pagination
        """

        page_size = 10  # results per page
        locations_client = LocationsClient()
        locations: List = locations_client.get_location_list(person_id, start_date, end_date)

        # Cache all users in memory for quick lookup
        person_map: Dict[str, Person] = {person.id: person for person in PersonService.retrieve_all()}

        data: List[Connection] = []

        query = db.session.query(Location)

        conditions = []

        for loc in locations:
            conditions.append(and_(
                text(
                    f"ST_DWithin(coordinate::geography,ST_SetSRID(ST_MakePoint({loc.get('latitude')},{loc.get('longitude')}),4326)::geography, {meters})")
                ,
                Location.person_id != int(person_id),
                start_date <= Location.creation_time,
                end_date + timedelta(days=1) > Location.creation_time,
            )
            )

        query = query \
            .filter(or_(*conditions)) \
            .distinct() \
            .limit(page_size) \
            .offset(page_size * (page - 1))

        for result in query:
            result.set_wkt_with_coords(result.latitude, result.longitude)

            data.append(
                Connection(
                    person=person_map.get(result.person_id), location=result,
                )
            )

        return data


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
