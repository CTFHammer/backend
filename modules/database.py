import pymongo
from pymongo import MongoClient


def get_db():
    client = MongoClient("mongodb://localhost:27017/")
    return client.mydatabase


class ProjectManager:
    def __init__(self, project_name):
        self.db = get_db()
        self.name = project_name
        self.collection = self.db.projects
        self.find_name = {'name': project_name}

    def insert_project(self):
        if self.collection.count_documents(self.find_name) == 0:
            return self.collection.insert_one(self.find_name)

    def find_project(self):
        return self.collection.find_one(self.find_name)

    def save_project(self, project):
        return self.collection.update_one(self.find_name, {'$set': project}, upsert=True)

    def add_pcap(self, pcap_file):
        self.collection.update_one(self.find_name, {'$push': {'pcap_files': pcap_file}})

    def remove_pcap(self, pcap_file):
        self.collection.update_one(self.find_name, {'$pull': {'pcap_files': pcap_file}})

    def set_port(self, port):
        self.collection.update_one(self.find_name, {'$set': {'port': port}})



def load_settings():
    try:
        settings = get_db().settings.find_one({'_id': 'unique_settings_id'})
        return settings if settings else {}
    except Exception as e:
        return {"error": str(e)}


def list_projects():
    return get_db().collection.find().sort('name', pymongo.ASCENDING)