from typing import Optional
from bson import ObjectId
import shutil
from modules.Managers.PcapManager import PCAPManager
from modules.config import PCAP_DIR
from modules.database import load_settings


class Project:
    def __init__(self, name: str, port: int = 0):
        self.name = name
        self.max_conversation_for_file = 50
        self.port = port

        # Init PCAPManager
        self.pcap_manager = PCAPManager(f"./{PCAP_DIR}/{name}", name, self)

    @staticmethod
    def parse(project) -> dict:
        parsed_project = {}
        for key, value in project.items():
            if isinstance(value, ObjectId):
                new_key = 'id' if key == '_id' else key
                parsed_project[new_key] = str(value)
            else:
                new_key = 'id' if key == '_id' else key
                parsed_project[new_key] = value
        return parsed_project

    def add_pcap(self, pcap_file):
        self.pcap_manager.add_pcap(pcap_file)

    def remove_pcap(self, pcap_file):
        self.pcap_manager.remove_pcap(pcap_file)

    def set_port(self, port: int) -> None:
        self.manager.set_port(port)

    def toJSON(self) -> dict:
        return {
            'name': self.name,
            'port': self.port,
        }

    def delete(self):
        try:
            shutil.rmtree(f'{PCAP_DIR}/{self.name}', ignore_errors=True)
        except FileNotFoundError:
            print("Folder doesn't exist")

    @staticmethod
    def from_dict(source):
        # Assumiamo che 'source' sia un dizionario con chiavi 'name' e 'port'
        return Project(name=source.get('name', ''), port=source.get('port', 0))

    # def start_tcp_dump(self):
    #     settings = load_settings()
    #     def run_tcpdump():
    #         ssh_client = create_ssh_client(settings["server_vul"], settings["port_vul"], settings["user"], settings["password"])
    #
    #         # Check folder
    #         folder_path = f"/pcap/{self.name}"
    #         check_and_create = f"mkdir -p {folder_path} && chmod 777 {folder_path}"
    #         execute_remote_command(ssh_client, check_and_create)
    #
    #         command = f"tcpdump -i any -G 10 -w {folder_path}/dump-%H-%M-%S.pcap"
    #         execute_remote_command(ssh_client, command)
    #
    #     # Avvia il thread
    #     thread = threading.Thread(target=run_tcpdump)
    #     thread.start()
    #
    #     thread2 = threading.Thread(target=periodic_sync, args=(settings, self.name))
    #     thread2.start()
    #
    #     return {"apposto": "cari ragazzi"}
