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
