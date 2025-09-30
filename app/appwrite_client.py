import os
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.users import Users

# Shared setup
def get_base_client(api_key):
    client = Client()
    client.set_endpoint("https://cloud.appwrite.io/v1")  # change if self-hosted
    client.set_project(os.getenv("APPWRITE_PROJECT_ID"))
    client.set_key(api_key)
    return client

# Database client (Products, Sales)
db_client = get_base_client(os.getenv("APPWRITE_API_KEY"))
databases = Databases(db_client)

# Auth client (Users, Sessions)
auth_client = get_base_client(os.getenv("APPWRITE_AUTH_API_KEY"))
users = Users(auth_client)
