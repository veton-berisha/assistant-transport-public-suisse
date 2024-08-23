import json
import os
import pandas as pd
import time

from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from pymongo import InsertOne, MongoClient, GEOSPHERE, WriteConcern


load_dotenv()


# Connexion à la base de données MongoDB
mongo_client = MongoClient(os.getenv('MONGO_URI'))
db = mongo_client[os.getenv('MONGO_DB')].with_options(write_concern=WriteConcern(w=0))

# Configurer un WriteConcern faible pour certaines collections
stop_times_collection = db['stop_times'].with_options(write_concern=WriteConcern(w=0))
trips_collection = db['trips'].with_options(write_concern=WriteConcern(w=0))
calendar_dates_collection = db['calendar_dates'].with_options(write_concern=WriteConcern(w=0))


def create_indexes():
    '''
    Créer les index pour les collections pour optimiser les performances
    '''
    db.agency.create_index([("agency_id", 1)])
    db.stops.create_index([("stop_id", 1), ("stop_name", 1)])
    db.routes.create_index([("route_id", 1), ("route_short_name", 1)])
    db.trips.create_index([("trip_id", 1), ("route_id", 1), ("service_id", 1), ("trip_headsign", 1)])
    db.stop_times.create_index([("trip_id", 1), ("stop_id", 1), ("departure_time", 1)])
    db.trip_updates.create_index([("trip_id", 1)])
    db.calendar_dates.create_index([("service_id", 1), ("date", 1)])
    db.calendar.create_index([("service_id", 1)])
    db.transfers.create_index([("from_stop_id", 1), ("to_stop_id", 1)])
    db.stops.create_index([("location", GEOSPHERE)])
    print("Indexes created successfully")


def insert_data_in_chunks(file_path, collection, chunksize=50000):
    '''
    Insérer les données en chunks pour optimiser les performances
    '''
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        for chunk in pd.read_csv(file, chunksize=chunksize):
            operations = [InsertOne(row) for row in chunk.to_dict(orient='records')]
            collection.bulk_write(operations, ordered=False)
            print(f"{len(chunk)} records insérés dans {collection.name}")


def insert_agency():
    insert_data_in_chunks('etl/gtfs_data/agency.txt', db.agency)


def insert_routes():
    insert_data_in_chunks('etl/gtfs_data/routes.txt', db.routes)


def insert_stops():
    '''
    Insérer les données des arrêts en chunks pour optimiser les performances et ajouter un index géospatial
    '''
    stops_iter = pd.read_csv('etl/gtfs_data/stops.txt', encoding='utf-8-sig', chunksize=10000)

    for chunk in stops_iter:
        # Convertir les colonnes de latitude et de longitude en numériques
        chunk['stop_lat'] = pd.to_numeric(chunk['stop_lat'], errors='coerce')
        chunk['stop_lon'] = pd.to_numeric(chunk['stop_lon'], errors='coerce')
        
        # Supprimer les lignes avec des valeurs NaN dans stop_lat ou stop_lon
        chunk = chunk.dropna(subset=['stop_lat', 'stop_lon'])
        
        # Filtrer les coordonnées géographiques valides
        chunk = chunk[(chunk['stop_lat'].between(-90, 90)) & (chunk['stop_lon'].between(-180, 180))]
        
        # Créer le champ `location` en format GeoJSON pour MongoDB
        chunk['location'] = chunk.apply(lambda x: {
            "type": "Point",
            "coordinates": [x['stop_lon'], x['stop_lat']]
        }, axis=1)
        
        # Remplir les valeurs manquantes
        chunk.fillna({'location_type': '0', 'parent_station': ''}, inplace=True)
        
        # Préparer les opérations pour l'insertion
        operations = [InsertOne(row) for row in chunk.to_dict(orient='records')]
        
        # Exécuter l'insertion en bulk
        db.stops.bulk_write(operations, ordered=False)
        print(f"{len(chunk)} stops insérés")


def insert_trips():
    insert_data_in_chunks('etl/gtfs_data/trips.txt', trips_collection)


def insert_stop_times():
    insert_data_in_chunks('etl/gtfs_data/stop_times.txt', stop_times_collection)


def insert_transfers():
    insert_data_in_chunks('etl/gtfs_data/transfers.txt', db.transfers)


def insert_calendar():
    insert_data_in_chunks('etl/gtfs_data/calendar.txt', db.calendar)


def insert_calendar_dates():
    insert_data_in_chunks('etl/gtfs_data/calendar_dates.txt', calendar_dates_collection)


def insert_realtime_data(file_path, collection):
    '''
    Insérer les données GTFS Realtime dans la collection spécifiée
    '''
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        if not data:
            print(f"Aucune donnée trouvée dans {file_path}")
        else:
            collection.insert_many(data)
            print(f'Données GTFS Realtime insérées depuis {file_path}')


def import_gtfs_data():
    '''
    Importer les données GTFS statiques et en temps réel dans la base de données MongoDB
    '''
    # Drop l'entièreté de la base de données
    mongo_client.drop_database(os.getenv('MONGO_DB'))
    print('Database dropped')

    start_time = time.time()
    print('Démarrage de l\'insertion des données GTFS à :', time.ctime())

    # Insertion des données statiques
    insert_agency()
    insert_routes()
    insert_stops()
    insert_transfers()
    insert_calendar()

    # Insertion des données statiques en parallèle
    with ThreadPoolExecutor(max_workers=8) as executor:
        executor.submit(insert_stop_times)
        executor.submit(insert_trips)
        executor.submit(insert_calendar_dates)

    # Insertion des données en temps réel
    insert_realtime_data('etl/gtfs_rt_data/trip_updates.json', db.trip_updates)

    # Créer les index après l'insertion
    create_indexes()

    print(f'Insertion des données GTFS terminée en {time.time() - start_time} secondes')
    print('Fin de l\'insertion des données GTFS à :', time.ctime())


if __name__ == '__main__':
    import_gtfs_data()
