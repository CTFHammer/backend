import pymongo
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from modules.config import mongo


def get_db():
    client = mongo.db
    return client


def load_settings():
    try:
        settings = get_db().settings.find_one({'_id': 'unique_settings_id'})
        if settings is not None:
            return settings
        else:
            raise ValueError("No settings found")
    except PyMongoError as e:
        raise Exception("Database error occurred") from e


def save_settings(settings):
    try:
        result = get_db().settings.update_one(
            {'_id': 'unique_settings_id'},
            {'$set': settings},
            upsert=True
        )
        if result.upserted_id or result.matched_count:
            return {"success": "Settings saved successfully", "id": result.upserted_id or 'existing'}
        else:
            return {"warning": "No settings were updated"}
    except Exception as e:
        return {"error": str(e)}


def list_projects():
    return get_db().collection.find().sort('name', pymongo.ASCENDING)
