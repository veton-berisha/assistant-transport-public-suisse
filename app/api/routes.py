from fastapi import APIRouter, Query

from app.api.chatbot import ask_gpt, UserQuery
from app.api.config import db
from app.api.trip import get_trip, TripRequestModel
from app.api.utils import search_stops, get_coordinates_from_address, find_nearest_stop


router = APIRouter()


@router.get("/search_stops")
async def search_stops_route(query: str = Query(None, min_length=3)):
    '''
    Rechercher des arrêts par nom et retourner une liste d'arrêts uniques
    '''
    return search_stops(db.stops, query)


@router.post("/trip")
def get_trip_route(request: TripRequestModel):
    '''
    Obtenir les détails du trajet entre deux arrêts à une date et une heure spécifiques
    '''
    return get_trip(request)


@router.post("/ask")
async def ask_gpt_route(user_query: UserQuery):
    '''
    Obtenir une réponse à partir d'une requête utilisateur en utilisant GPT
    '''
    return await ask_gpt(user_query)


@router.get("/nearest_stops")
async def get_nearest_stop(query: str):
    '''
    Obtenir les arrêts les plus proches d'une position géographique donnée
    '''
    coordinates = get_coordinates_from_address(query)
    if coordinates:
        return find_nearest_stop(*coordinates)
    return None
