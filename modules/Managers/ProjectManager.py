from typing import Optional, TYPE_CHECKING, TypeVar

from celery import shared_task

from modules.Managers.SSHManager import ssh_form_settings, execute_command, load_form_settings, \
    execute_background_command, download_files_scp
from modules.config import PCAP_DIR
from modules.database import get_db, load_settings
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
        return self.collection.update_one({"name": project_name}, {'$set': project}, upsert=True)

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


def find_project(project_name):
    db = get_db()
    return db.projects.find_one({"name": project_name})


# @shared_task()
def start_tcp_dump(project_name: str):
    settings = load_settings()
    project = find_project(project_name)
    client = load_form_settings(settings)
    if client is False:
        return {"status": False, "message": "SSH client is not available"}

    if 'port' not in project:
        return {"status": False, "message": "We need a port for TCP dump"}

    pcap_dir = f"{PCAP_DIR}/{project_name}"

    command = f"tshark -i any -w {pcap_dir}/out.pcap -f \"port {project['port']}\" -b \"duration:10\""
    execute_command(client, f"mkdir -p {pcap_dir}")
    pid = execute_background_command(client, command)

    client.close()

    return {"status": True, "message": "TCP dump started successfully", "pid": pid}


def stop_tcp_dump(project_name: str):
    project = find_project(project_name)
    settings = load_settings()
    if "pid_tcpdump" in project:
        client = load_form_settings(settings)
        pid = project["pid_tcpdump"]
        out, _ = execute_command(client, f"kill -9 {pid}")
        client.close()
        return {"status": True, "message": "TCP dump stopped", "pid": pid}
    else:
        return {"status": False, "message": "noting to stop"}


def download_pcap(project_name: str):
    settings = load_settings()
    pcap_dir = f"{PCAP_DIR}/{project_name}"
    client = load_form_settings(settings)
    download_files_scp(client, pcap_dir, PCAP_DIR)
    execute_command(client, f"rm -r {pcap_dir}/*")
    client.close()
