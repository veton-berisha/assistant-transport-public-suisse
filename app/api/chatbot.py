from datetime import datetime
from pydantic import BaseModel
from typing import Dict

from app.api.utils import get_coordinates_from_address, find_nearest_stop, verify_stop_exists
from app.api.config import openai_client
from app.api.trip import get_trip, TripRequestModel


# Dictionnaire pour stocker les conversations en cours
conversations: Dict[str, Dict] = {}


class UserQuery(BaseModel):
    '''
    Modèle de données pour les requêtes utilisateur
    '''
    query: str
    session_id: str


def initialize_conversation(session_id: str):
    """
    Initialise une nouvelle conversation avec un message de bienvenue
    """
    conversations[session_id] = {
        "steps": {
            "origin": None,
            "destination": None,
            "date": None,
            "time": None,
        },
        "conversation_history": [
            {"role": "assistant", "content": "Bonjour, je suis votre assistant virtuel des transports publics Suisse (TP-Suisse). 🚂🚌🚋⛴️\nPour connaître le nom exact d'un arrêt, veuillez cliquer sur la bulle de chat ci-dessous. 💬\n Pour arrêter/recommencer la conversation, écrivez 'STOP' ou rafrachissez la page. 🛑\nOù desirez-vous aller ? 🌍"}
        ],
        "count_trip_details": 0
    }


def generate_response(conversation_history, prompt, max_tokens=150):
    """
    Génère une réponse en utilisant GPT
    """
    gpt_response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history + [{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.7
    )
    return gpt_response.choices[0].message.content.strip()


def handle_conversation_steps(user_input, steps, conversation_history):
    """
    Gère les différentes étapes de la conversation en fonction des informations fournies par l'utilisateur
    """
    if not steps["destination"] or steps["destination"] is None:
        return process_destination_step(user_input, steps, conversation_history)

    if not steps["origin"] or steps["origin"] is None:
        return process_origin_step(user_input, steps, conversation_history)

    if not steps["date"] or not steps["time"] or steps["date"] is None or steps["time"] is None:
        return process_date_time_step(user_input, steps, conversation_history)


def process_destination_step(user_input, steps, conversation_history):
    """
    Traite l'étape où l'utilisateur spécifie sa destination
    """
    gpt_help = generate_response(conversation_history, f"L'utilisateur a surement mentionné une destination dans {user_input}. Met l'arret entre deux # pour l'extraire. Souvent, il y a le nom de la ville ou commune virgule puis l'arrêt : #Ville, Arrêt#. Apart ce qu'il y a entre les #, tu peux ignorer le reste. Si tu penses que c'est une adresse, un monument ou un lieu spécifique, tu mets le maximum d'informations pour trouver l'arrêt le plus proche (surtout la ville ou commune) sans oublier les # mais pas besoin de structure spécifique comme pour l'arret : #Ville, Arrêt#.")
    if "#" in gpt_help:
        stop_name = gpt_help.split("#")[1]
        verified_stop = verify_stop_exists(stop_name)
        if verified_stop:
            steps["destination"] = verified_stop
            return generate_response(conversation_history, f"L'utilisateur a mentionné {verified_stop} comme destination. Formule une réponse pour informer que l'arrêt est sélectionné et enchainer la suite de la conversation avec le point de départ.")
        else:
            coordinates = get_coordinates_from_address(stop_name)
            if coordinates:
                nearest_stop = find_nearest_stop(*coordinates)
                if nearest_stop is not None:
                    steps["destination"] = nearest_stop
                    return generate_response(conversation_history, f"L'utilisateur a mentionné {stop_name} comme destination. Je n'ai pas trouvé l'arrêt exact directement, mais j'ai trouvé l'arrêt le plus proche: {nearest_stop} grâce à une recherche des coordonnées. Formule une réponse pour informer que l'arrêt est sélectionné et enchainer la suite de la conversation avec le point de départ.")
                else:
                    return generate_response(conversation_history, "La destination mentionnée par l'utilisateur n'a pas été trouvée malgré une recherche des coordonnées. Demande-lui de préciser, d'utiliser la bulle de chat pour trouver l'arrêt exact ou de réessayer avec un autre arrêt.")
            else:
                return generate_response(conversation_history, "L'utilisateur a mentionné une destination que je n'ai pas trouvée. Demande-lui de préciser, d'utiliser la bulle de chat pour trouver l'arrêt exact ou de réessayer avec un autre arrêt.")
    else:
        return generate_response(conversation_history, "L'utilisateur a mentionné une destination que je n'ai pas trouvée. Demande-lui de préciser ou de réessayer avec un autre arrêt pour la destination afin de continuer.")


def process_origin_step(user_input, steps, conversation_history):
    """
    Traite l'étape où l'utilisateur spécifie son point de départ
    """
    gpt_help = generate_response(conversation_history, f"L'utilisateur a surement mentionné un point de départ dans {user_input}. Met l'arret entre deux # pour l'extraire. Souvent, il y a le nom de la ville ou commune virgule puis l'arrêt : #Ville, Arrêt#. Apart ce qu'il y a entre les #, tu peux ignorer le reste. Si tu penses que c'est une adresse, un monument ou un lieu spécifique, tu mets le maximum d'informations pour trouver l'arrêt le plus proche (surtout la ville ou commune) sans oublier les # mais pas besoin de structure spécifique comme pour l'arret : #Ville, Arrêt#.")
    if "#" in gpt_help:
        stop_name = gpt_help.split("#")[1]
        verified_stop = verify_stop_exists(stop_name)
        if verified_stop:
            steps["origin"] = verified_stop
            return generate_response(conversation_history, f"L'utilisateur a mentionné {verified_stop} comme point de départ. Formule une réponse pour informer que l'arrêt est sélectionné et demander la date et l'heure.")
        else:
            coordinates = get_coordinates_from_address(stop_name)
            if coordinates:
                nearest_stop = find_nearest_stop(*coordinates)
                if nearest_stop is not None:
                    steps["origin"] = nearest_stop
                    return generate_response(conversation_history, f"L'utilisateur a mentionné {stop_name} comme point de départ. Je n'ai pas trouvé l'arrêt exact directement, mais j'ai trouvé l'arrêt le plus proche: {nearest_stop} grâce à une recherche des coordonnées. Formule une réponse pour informer que l'arrêt est sélectionné et demander la date et l'heure.")
                else:
                    return generate_response(conversation_history, "L'utilisateur a mentionné un arrêt de départ que je n'ai pas trouvé malgré une recherche des coordonnées. Demande-lui de préciser, d'utiliser la bulle de chat pour trouver l'arrêt exact ou de réessayer avec un autre arrêt.")
            else:
                return generate_response(conversation_history, "L'utilisateur a mentionné un arrêt de départ que je n'ai pas trouvé. Demande-lui de préciser, d'utiliser la bulle de chat pour trouver l'arrêt exact ou de réessayer avec un autre arrêt.")
    else:
        return generate_response(conversation_history, "L'utilisateur a mentionné un arrêt de départ que je n'ai pas trouvé. Demande-lui de préciser ou de réessayer avec un autre arrêt.")


def process_date_time_step(user_input, steps, conversation_history):
    """
    Traite l'étape où l'utilisateur spécifie la date et l'heure
    """
    gpt_help = generate_response(conversation_history, f"L'utilisateur a mentionné une date et une heure dans '{user_input}'. Pour information, la date du jour est {datetime.now().strftime('%Y-%m-%d')} et l'heure est {datetime.now().strftime('%H:%M:%S')}. Met la date entre deux # pour l'extraire et l'heure entre deux $. Tu peux écrire seulement la date et/ou l'heure, pas besoin d'autres informations. Le format de la date est 'YYYY-MM-DD' et l'heure 'HH:MM:SS'.")

    # Extraire date et heure selon les délimiteurs '#' et '$'
    date_str = None
    time_str = None

    if "#" in gpt_help:
        date_str = gpt_help.split("#")[1]

    if "$" in gpt_help:
        time_str = gpt_help.split("$")[1]

    if date_str and time_str:
        steps["date"] = date_str
        steps["time"] = time_str
        return generate_response(conversation_history, f"L'utilisateur a spécifié la date {steps['date']} et l'heure {steps['time']}. Faire un petit récapitulatif et dire si l'utilisateur est d'accord pour lancer la recherche.")

    elif date_str:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            steps["date"] = date_str
            return generate_response(conversation_history, f"L'utilisateur a spécifié la date {steps['date']}. Veuillez demander maintenant l'heure exacte de départ.")
        except ValueError:
            return generate_response(conversation_history, "Je n'ai pas compris la date. Pouvez-vous reformuler, s'il vous plaît ?")
    elif time_str:
        try:
            datetime.strptime(time_str, "%H:%M:%S")
            steps["time"] = time_str
            return generate_response(conversation_history, f"L'utilisateur a spécifié l'heure {steps['time']}. Veuillez demander maintenant la date exacte.")
        except ValueError:
            return generate_response(conversation_history, "Je n'ai pas compris l'heure. Pouvez-vous reformuler, s'il vous plaît ?")
    else:
        return generate_response(conversation_history, "Je n'ai pas bien compris la date ou l'heure. Pouvez-vous reformuler, s'il vous plaît ?")


def process_trip_request(steps, session_id, conversation_history):
    """
    Envoie une requête pour récupérer les détails du voyage et les formate
    """
    trip_request_data = {
        "origin_name": steps['origin'],
        "destination_name": steps['destination'],
        "date": steps['date'],
        "time": steps['time']
    }
    trip_request = TripRequestModel(**trip_request_data)
    response = get_trip(trip_request)

    if response.get("trip_details"):
        trip_details = response["trip_details"]
        gpt_reply = generate_response(
            conversation_history,
            f"Voici les détails du voyage récupérés: {trip_details}, il faut que l'affichage soit facile à lire pour l'utilisateur, donc formate en Markdown afin que ça soit propre (titre avec niveau, gras, italique, etc.). Propose 3 trajets maximum. Il est important de fournir des informations claires et précises pour le voyage demandé (heure de départ, heure d'arrivée, correspondances, etc.). Formule une réponse polie et engageante avec une suggestion pour un nouveau voyage. Dire que l'utilisateur peut demander une nouvelle recherche car c'est fini pour ce voyage.",
            max_tokens=800
        )

        # Réinitialiser les étapes et l'historique de la conversation
        conversations[session_id] = {
            "steps": {
                "origin": None,
                "destination": None,
                "date": None,
                "time": None,
            },
            "conversation_history": [],
            "count_trip_details": 0
        }

        return gpt_reply

    else:
        conversations[session_id]["count_trip_details"] += 1
        return generate_response(conversation_history, f"Une erreur s'est produite lors de la récupération des détails du voyage. Demande à l'utilisateur s'il veut réessayer ou arrêter le processus. Reponse de la requete: {response.get('response')}.")


async def ask_gpt(user_query: UserQuery):
    """
    Fonction pour gérer les requêtes utilisateur et les réponses de GPT pour une conversation sur les transports publics
    """
    session_id = user_query.session_id

    if session_id not in conversations:
        initialize_conversation(session_id)

    user_input = user_query.query
    steps = conversations[session_id]["steps"]
    conversation_history = conversations[session_id]["conversation_history"]

    # Ajouter l'entrée utilisateur à l'historique
    conversation_history.append({"role": "user", "content": user_input})

    if "stop" in user_input.lower():
        gpt_reply = generate_response(conversation_history, "Merci pour votre visite. N'hésitez pas à relancer une demande de planification de voyage si vous avez besoin d'aide. À bientôt ! 👋")
        del conversations[session_id]
        return {"gpt_answer": gpt_reply, "session_id": session_id}

    # Gestion des étapes de la conversation
    gpt_reply = handle_conversation_steps(user_input, steps, conversation_history)

    # Si toutes les informations sont collectées
    if all(steps.values()):
        gpt_reply = process_trip_request(steps, session_id, conversation_history)

    # Ajouter la réponse de GPT à l'historique
    conversation_history.append({"role": "assistant", "content": gpt_reply})

    return {"gpt_answer": gpt_reply, "session_id": session_id}
