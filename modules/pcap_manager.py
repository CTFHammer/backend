import glob
import json
import os
import time
from datetime import time
from modules.analyzePcap import analyze_conversation
from modules.config import PCAP_DIR
from modules.database import get_db


class PCAPManager:
    def __init__(self, project_dir, project_name, project_manager):
        # Check if dir exists
        self.project_dir = os.path.join(PCAP_DIR, project_dir)
        self.project_name = project_name
        self.project_manager = project_manager
        if not os.path.exists(self.project_dir):
            os.makedirs(self.project_dir)

        self.pcap_files = []
        print(self.project_dir)


    def add_pcap(self, pcap_file):
        self.pcap_files.append(pcap_file)
        self.project_manager.add_pcap(pcap_file)


    def remove_pcap(self, pcap_file):
        os.remove(pcap_file)
        self.project_manager.db_manager.remove_pcap(pcap_file)


    def analyze_local_pcap(self, folder_path):
        while True:
            for filepath in glob.glob(os.path.join(folder_path, '*.pcap')):
                conversations = analyze_conversation(filepath, self.project_name, self.port, 100)
                from socketManager import socketio
                conversations_serializable = json.dumps(conversations)
                socketio.emit("analyze_pcap", {"project_name": self.project_name, "conversations": conversations_serializable}, to=None)
                self.remove_pcap(filepath)
            time.sleep(10)







class PCAPDatabse:
    def __init__(self):
        self.db = get_db()


