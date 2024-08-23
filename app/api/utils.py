import requests

from datetime import datetime
from fastapi import HTTPException
from pymongo.collection import Collection
from typing import List, Dict

from app.api.config import db


def format_datetime(datetime_str):
    '''
    Formater une date et heure au format "dd.mm.yyyy HH:MM:SS"
    '''
    dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ")
    return dt.strftime("%d.%m.%Y %H:%M:%S")


def find_stop_id(stop_name: str):
    '''
    Rechercher un arrêt par son nom et retourner son ID et son nom
    '''
    stop = db.stops.find_one({"stop_name": {"$regex": f"^{stop_name}$", "$options": "i"}})
    if stop:
        return stop["stop_id"], stop["stop_name"]
    else:
        raise HTTPException(status_code=404, detail=f"Stop '{stop_name}' not found")


def verify_stop_exists(stop_name: str):
    '''
    Vérifier si un arrêt existe dans la base de données
    '''
    stop = db.stops.find_one({"stop_name": {"$regex": f"^{stop_name}$", "$options": "i"}})
    if stop:
        return stop['stop_name']
    return None


def search_stops(db_collection: Collection, query: str) -> List[Dict[str, str]]:
    '''
    Rechercher des arrêts par nom et retourner une liste d'arrêts uniques
    '''
    stops_cursor = db_collection.find({"stop_name": {"$regex": query, "$options": "i"}})
    stops = list(stops_cursor)
    unique_stops = {}

    for stop in stops:
        stop_name = stop["stop_name"]
        if stop_name not in unique_stops:
            unique_stops[stop_name] = stop

    return [{"stop_name": stop["stop_name"]} for stop in unique_stops.values()]


def get_coordinates_from_address(address):
    """
    Utilise l'API Nominatim d'OpenStreetMap pour obtenir les coordonnées (latitude et longitude) d'une adresse donnée.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address,
        'format': 'json',
        'limit': 1,
        'countrycodes': 'CH',
        'accept-language': 'fr'
    }
    headers = {
        'User-Agent': 'API Client'
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200 and response.json():
        result = response.json()[0]
        return float(result['lat']), float(result['lon'])
    else:
        return None


def find_nearest_stop(latitude, longitude):
    """
    Trouve l'arrêt de bus le plus proche dans MongoDB à partir de coordonnées géographiques.
    """
    location_requested = [longitude, latitude]

    nearest_stop = db.stops.find_one({
        "location": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": location_requested
                }
            }
        }
    })

    if nearest_stop:
        return nearest_stop['stop_name']
    else:
        return None
