import requests

from datetime import datetime
from fastapi import HTTPException
from pydantic import BaseModel
from xml.etree import ElementTree as ET

from app.api.config import ojp_api_key, ojp_api_url
from app.api.utils import find_stop_id, format_datetime


class TripRequestModel(BaseModel):
    '''
    Modèle de données pour les détails du trajet
    '''
    origin_name: str
    destination_name: str
    date: str  # En format string pour l'API OJP
    time: str  # En format string pour l'API OJP


def parse_response(response_xml):
    '''
    Analyser la réponse XML de l'API OJP et extraire les détails du trajet pour chaque itinéraire trouvé
    '''
    # Parse the XML response
    root = ET.fromstring(response_xml)

    trip_details = []
    trip_counter = 1

    # Extraire les détails de chaque trajet
    for trip in root.findall(".//ojp:Trip", namespaces={"ojp": "http://www.vdv.de/ojp"}):

        trip_description = [f"Trajet n°{trip_counter}:"]  # Initialiser la description du trajet

        # Extraire les détails de chaque étape du trajet
        for leg in trip.findall(".//ojp:TimedLeg", namespaces={"ojp": "http://www.vdv.de/ojp"}):
            origin_stop_name_elem = leg.find(".//ns0:LegBoard/ns0:StopPointName/ns0:Text", namespaces={"ns0": "http://www.vdv.de/ojp"})
            origin_stop_name = origin_stop_name_elem.text if origin_stop_name_elem is not None else "Unknown"

            departure_time_elem = leg.find(".//ns0:LegBoard/ns0:ServiceDeparture/ns0:TimetabledTime", namespaces={"ns0": "http://www.vdv.de/ojp"})
            departure_time = format_datetime(departure_time_elem.text) if departure_time_elem is not None else "Unknown"

            destination_stop_name_elem = leg.find(".//ns0:LegAlight/ns0:StopPointName/ns0:Text", namespaces={"ns0": "http://www.vdv.de/ojp"})
            destination_stop_name = destination_stop_name_elem.text if destination_stop_name_elem is not None else "Unknown"

            arrival_time_elem = leg.find(".//ns0:LegAlight/ns0:ServiceArrival/ns0:TimetabledTime", namespaces={"ns0": "http://www.vdv.de/ojp"})
            arrival_time = format_datetime(arrival_time_elem.text) if arrival_time_elem is not None else "Unknown"

            line_elem = leg.find(".//ns0:Service/ns0:PublishedLineName/ns0:Text", namespaces={"ns0": "http://www.vdv.de/ojp"})
            line = line_elem.text if line_elem is not None else "Unknown line"

            destination_line_elem = leg.find(".//ns0:Service/ns0:DestinationText/ns0:Text", namespaces={"ns0": "http://www.vdv.de/ojp"})
            destination_line = destination_line_elem.text if destination_line_elem is not None else "Unknown destination"

            # Ajouter les détails de l'étape du trajet à la description du trajet
            trip_description.append(
                f"Prenez la ligne {line} (direction {destination_line}) de {origin_stop_name} à {departure_time}, puis descendez à {destination_stop_name} à {arrival_time}."
            )

        # Combiner les détails du trajet en une seule chaîne de caractères
        full_trip_description = " ".join(trip_description)
        trip_details.append(full_trip_description)

        trip_counter += 1  # Incrémenter le compteur de trajet pour le prochain trajet

    return trip_details


def create_trip_request_xml(origin_stop_id, origin_name, destination_stop_id, destination_name, date_time_iso):
    '''
    Créer une requête XML pour l'API OJP à partir des détails du trajet
    '''
    return f"""
    <OJP xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
    xmlns="http://www.siri.org.uk/siri" version="1.0" xmlns:ojp="http://www.vdv.de/ojp" xsi:schemaLocation="http://www.siri.org.uk/siri ../ojp-xsd-v1.0/OJP.xsd">
        <OJPRequest>
            <ServiceRequest>
                <RequestTimestamp>{date_time_iso}</RequestTimestamp>
                <RequestorRef>{ojp_api_key}_prod</RequestorRef>
                <ojp:OJPTripRequest>
                    <RequestTimestamp>{date_time_iso}</RequestTimestamp>
                    <ojp:Origin>
                        <ojp:PlaceRef>
                            <ojp:StopPlaceRef>{origin_stop_id}</ojp:StopPlaceRef>
                            <ojp:LocationName>
                                <ojp:Text>{origin_name}</ojp:Text>
                            </ojp:LocationName>
                        </ojp:PlaceRef>
                        <ojp:DepArrTime>{date_time_iso}</ojp:DepArrTime>
                    </ojp:Origin>
                    <ojp:Destination>
                        <ojp:PlaceRef>
                            <ojp:StopPlaceRef>{destination_stop_id}</ojp:StopPlaceRef>
                            <ojp:LocationName>
                                <ojp:Text>{destination_name}</ojp:Text>
                            </ojp:LocationName>
                        </ojp:PlaceRef>
                    </ojp:Destination>
                    <ojp:Params>
                        <ojp:NumberOfResults>10</ojp:NumberOfResults>
                        <ojp:OptimisationMethod>fastest</ojp:OptimisationMethod>
                        <ojp:IncludeTrackSections>true</ojp:IncludeTrackSections>
                        <ojp:IncludeTurnDescription>true</ojp:IncludeTurnDescription>
                        <ojp:IncludeIntermediateStops>true</ojp:IncludeIntermediateStops>
                    </ojp:Params>
                </ojp:OJPTripRequest>
            </ServiceRequest>
        </OJPRequest>
    </OJP>
    """


def get_trip(trip_request: TripRequestModel):
    '''
    Obtenir les détails du trajet entre deux arrêts à une date et une heure spécifiques
    '''
    origin_stop_id, origin_name = find_stop_id(trip_request.origin_name)
    destination_stop_id, destination_name = find_stop_id(trip_request.destination_name)

    date_time_str = f"{trip_request.date}T{trip_request.time}"
    date_time_iso = datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S").isoformat() + "Z"

    ojp_request_xml = create_trip_request_xml(
        origin_stop_id,
        origin_name,
        destination_stop_id,
        destination_name,
        date_time_iso
    )

    headers = {
        'Content-Type': 'application/xml',
        'Authorization': f'Bearer {ojp_api_key}'
    }

    response = requests.post(ojp_api_url, data=ojp_request_xml, headers=headers)

    if response.status_code == 200:
        root = ET.fromstring(response.content)
        response_text = ET.tostring(root, encoding='unicode', method='xml')
        return {
            "response": response_text,
            "trip_details": parse_response(response.content)
        }
    else:
        return {
            "response": f"Error: {response.status_code} - {response.text}",
        }
