import json
import os
import requests

from dotenv import load_dotenv
from google.transit import gtfs_realtime_pb2


load_dotenv()


def get_gtfs_realtime_data():
    """
    Récupérer les données GTFS Realtime depuis l'API
    """
    token = os.getenv("GTFS_RT_TOKEN")
    gtfs_realtime_url = os.getenv("GTFS_RT_URL")

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(gtfs_realtime_url, headers=headers)
    if response.status_code == 200:
        return response.content
    else:
        print(f"Erreur lors de la récupération des données GTFS Realtime: {response.status_code} - {response.text}")
        return None


def parse_gtfs_realtime_data(data):
    """
    Analyser les données GTFS Realtime et les stocker dans des listes distinctes
    """
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(data)

    trip_updates = []

    print(f"Number of entities: {len(feed.entity)}")

    for entity in feed.entity:
        if entity.HasField('trip_update'):
            trip_update = entity.trip_update
            stop_time_updates = []
            for update in trip_update.stop_time_update:
                stop_time_updates.append({
                    'stop_id': update.stop_id,
                    'arrival': update.arrival.time if update.HasField('arrival') else None,
                    'departure': update.departure.time if update.HasField('departure') else None
                })
            trip_updates.append({
                'type': 'trip_update',
                'trip_id': trip_update.trip.trip_id,
                'route_id': trip_update.trip.route_id,
                'stop_time_updates': stop_time_updates
            })

    return {
        'trip_updates': trip_updates
    }


def save_data_to_json(data, filename):
    """
    Enregistrer les données GTFS Realtime dans un fichier JSON
    """
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f'Données GTFS Realtime enregistrées dans {filename}')


if __name__ == '__main__':
    # Récupérer les données GTFS Realtime
    realtime_data = get_gtfs_realtime_data()

    if realtime_data:
        # Analyser les données GTFS Realtime
        parsed_data = parse_gtfs_realtime_data(realtime_data)

        # Enregistrer les données dans des fichiers JSON
        save_data_to_json(parsed_data['trip_updates'], 'etl/gtfs_rt_data/trip_updates.json')
