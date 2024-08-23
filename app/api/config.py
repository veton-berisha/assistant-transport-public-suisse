import os

from dotenv import load_dotenv
from openai import OpenAI
from pymongo import MongoClient


load_dotenv()


# Connexion à MongoDB
mongo_client = MongoClient(os.getenv('MONGO_URI'))
db = mongo_client[os.getenv('MONGO_DB')]

# OpenAI API
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# OJP API URL et clé
ojp_api_key = os.getenv("OJP_API_TOKEN")
ojp_api_url = os.getenv("OJP_API_URL")
