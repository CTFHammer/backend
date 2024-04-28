from pymongo import MongoClient
from flask import g

client = MongoClient("mongodb://localhost:27017/")
db = client.mydatabase

def get_db():
    return db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.client.close()



def save_settings(settings):
    db.settings.update_one({'_id': 'unique_settings_id'}, {'$set': settings}, upsert=True)


def load_settings():
    try:
        settings = db.settings.find_one({'_id': 'unique_settings_id'})
        return settings if settings else {}
    except Exception as e:
        print(f"Failed to load settings: {e}")
        return {}

