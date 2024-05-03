import pymongo
from pymongo import MongoClient


def get_db():
    client = MongoClient("mongodb://localhost:27017/")
    return client.mydatabase



def load_settings():
    try:
        settings = get_db().settings.find_one({'_id': 'unique_settings_id'})
        return settings if settings else {}
    except Exception as e:
        return {"error": str(e)}


def save_settings(settings):
    try:
        settings = get_db().settings.update_one({'_id': 'unique_settings_id'}, {'$set': settings})
        return settings if settings else {}
    except Exception as e:
        return {"error": str(e)}


def list_projects():
    return get_db().collection.find().sort('name', pymongo.ASCENDING)