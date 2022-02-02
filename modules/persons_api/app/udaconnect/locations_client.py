from typing import List

import requests
from flask import json

from app.udaconnect.schemas import LocationSchema

LOCATIONS_PORT = "5001"
LOCATIONS_HOST = "localhost"


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

        locations = requests.get(f'http://{LOCATIONS_HOST}:{LOCATIONS_PORT}/locations_api/locations/persons/{person_id}?start_date={start_date}&end_date={end_date}', auth=('user', 'pass'))

        return locations.json()
