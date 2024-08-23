import os
import requests
import zipfile

from bs4 import BeautifulSoup
from dotenv import load_dotenv


load_dotenv()


def get_latest_zip_url():
    '''
    Obtenir l'URL du dernier fichier zip de données GTFS statiques
    '''
    # Obtenir l'URL du dernier fichier zip
    dataset_url = os.getenv('GTFS_STATIC_URL')
    response = requests.get(dataset_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Trouver la section contenant les ressources et les liens
    resources_section = soup.find('section', {'id': 'dataset-resources'})
    links = resources_section.find_all('a')

    # Filtrer pour trouver le dernier fichier zip
    for link in links:
        href = link.get('href')
        if href and href.endswith('.zip'):
            return href
    return None


def get_existing_zip_file(directory):
    '''
    Trouver le fichier zip existant dans le répertoire courant
    '''
    files = os.listdir(directory)
    zip_files = [f for f in files if f.endswith('.zip')]
    if zip_files:
        return zip_files[0]  # Assumons qu'il n'y a qu'un seul fichier zip
    return None


def extract_zip(zip_filename, directory):
    '''
    Extraire le contenu du fichier zip
    '''
    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        zip_ref.extractall(directory)
    print(f'Le fichier zip {zip_filename} a été extrait avec succès.')


def download_latest_zip():
    '''
    Télécharger le dernier fichier zip de données GTFS statiques
    '''
    zip_link = get_latest_zip_url()
    if zip_link:
        if not zip_link.startswith('http'):
            zip_url = 'https://opentransportdata.swiss' + zip_link
        else:
            zip_url = zip_link

        # Extraire le nom du fichier zip
        zip_filename = os.path.join('etl', 'gtfs_data', os.path.basename(zip_link))
        existing_zip = get_existing_zip_file('etl/gtfs_data')
        if existing_zip and existing_zip != zip_filename:
            # Télécharger le nouveau fichier zip
            zip_response = requests.get(zip_url)
            with open(zip_filename, 'wb') as f:
                f.write(zip_response.content)
            print(f'Le fichier zip {zip_filename} a été téléchargé avec succès.')

            # Supprimer l'ancien fichier zip
            os.remove(os.path.join('etl', 'gtfs_data', existing_zip))
            print(f'L\'ancien fichier zip {existing_zip} a été supprimé.')

            # Extraire le contenu du nouveau fichier zip
            extract_zip(zip_filename, 'etl/gtfs_data')

        elif not existing_zip:
            # Télécharger le fichier zip car aucun fichier existant n'a été trouvé
            zip_response = requests.get(zip_url)
            with open(zip_filename, 'wb') as f:
                f.write(zip_response.content)
            print(f'Le fichier zip {zip_filename} a été téléchargé avec succès.')

            # Extraire le contenu du nouveau fichier zip
            extract_zip(zip_filename, 'etl/gtfs_data')
        else:
            print(f'Le fichier existant {existing_zip} est déjà à jour.')
    else:
        print('Aucun fichier zip trouvé.')


if __name__ == '__main__':
    download_latest_zip()
