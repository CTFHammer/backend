from typing import Optional, TYPE_CHECKING, TypeVar
from modules.database import get_db
from modules.Models.ProjectModel import Project

T = TypeVar('T', bound='ProjectManager')


class ProjectManager:
    def __init__(self):
        self.db = get_db()
        self.collection = self.db.projects


    def exists(self, project_name: str) -> bool:
        return self.find_project(project_name) is not None


    def create_project_in_db(self, project_name: str):
        """Create a project in a database"""
        self.collection.insert_one({"name": project_name})
        print(f"Project {project_name} created in database.")


    def insert_project(self, project_name: str):
        if self.collection.count_documents(project_name) == 0:
            return self.collection.insert_one(project_name)


    def find_project(self, project_name: str) -> dict:
        return self.collection.find_one({"name": project_name})


    def save_project(self, project_name, project):
        return self.collection.update_one(project_name, {'$set': project}, upsert=True)


    def add_pcap(self, project_name: str, pcap_file):
        self.collection.update_one(project_name, {'$push': {'pcap_files': pcap_file}})


    def remove_pcap(self, project_name: str, pcap_file):
        self.collection.update_one(project_name, {'$pull': {'pcap_files': pcap_file}})


    def set_port(self, project_name: str, port: int):
        self.collection.update_one({"name": project_name}, {'$set': {'port': port}})


    def list_projects(self) -> list['Project']:
        cursor = self.collection.find()
        return [Project.parse(project) for project in cursor]


    def delete_project(self, project_name: str):
        print(self.collection.delete_one({"name": project_name}))