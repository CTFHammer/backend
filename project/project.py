import glob
import json
import os
import time
import threading

from bson import json_util
from flask import Blueprint, jsonify, request
from flask_cors import CORS
from pymongo import DESCENDING
from werkzeug.utils import secure_filename
from analyzePcap import analyze_conversation
from db import get_db, db, load_settings
from remoteCommand import create_ssh_client, execute_remote_command, copy_file_from_remote, periodic_sync
from socketManager import socketio
from watcher import Watcher, active_observers

PCAP_DIR = './projects'

# Creazione della Blueprint
project_blueprint = Blueprint('project', __name__)
CORS(project_blueprint)

class Project:
    def __init__(self, name):
        self.port = None
        self.db = get_db()
        self.name = name
        self.max_conversation_for_file = 50
        self.project_dir = os.path.join(PCAP_DIR, name)
        if not os.path.exists(self.project_dir):
            os.makedirs(self.project_dir)
        self.project_collection = self.db.projects
        self.pcap_files = []

        if self.project_collection.count_documents({'name': self.name}) == 0:
            self.project_collection.insert_one({'name': self.name, 'pcap_files': []})


    def add_pcap(self, pcap_file):
        filepath = os.path.join(self.project_dir, pcap_file)
        self.pcap_files.append(filepath)
        self.analyze_pcap(filepath)
        self.project_collection.update_one({'name': self.name}, {'$push': {'pcap_files': filepath}})


    def set_port(self, port):
        self.port = port
        self.project_collection.update_one({'name': self.name}, {'$set': {'port': self.port}})


    def serialize_datetime(self, obj):
        return json.loads(json_util.dumps(obj))


    def background_task(self, folder_path):
        while True:
            for filepath in glob.glob(os.path.join(folder_path, '*.pcap')):
                conversations = analyze_conversation(filepath, self.name, self.port, 100)
                from socketManager import socketio
                conversations_serializable = json.dumps(conversations, default=self.serialize_datetime)
                socketio.emit("analyze_pcap", {"project_name": self.name, "conversations": conversations_serializable}, to=None)
                self.project_collection.update_one({'name': self.name}, {'$pull': {'pcap_files': filepath}})
                os.remove(filepath)
            time.sleep(10)


    def analyze_pcap(self, folder_path):
        thread = threading.Thread(target=self.background_task, args=(folder_path,))
        thread.start()
        return {"result": "start analyzing"}


    @staticmethod
    def load(project_name):
        project_data = db.projects.find_one({'name': project_name})
        if project_data:
            project = Project(project_data['name'])
            project.pcap_files = project_data['pcap_files']
            project.port = project_data.get('port')
            return project
        return None


    def toJSON(self):
        return {
            'name': self.name,
            'port': self.port,
            'pcap_files': self.pcap_files,
        }


    def start_tcp_dump(self):
        settings = load_settings()
        def run_tcpdump():
            ssh_client = create_ssh_client(settings["server_vul"], settings["port_vul"], settings["user"], settings["password"])

            # Check folder
            folder_path = f"/pcap/{self.name}"
            check_and_create = f"mkdir -p {folder_path} && chmod 777 {folder_path}"
            execute_remote_command(ssh_client, check_and_create)

            command = f"tcpdump -i any -G 10 -w {folder_path}/dump-%H-%M-%S.pcap"
            execute_remote_command(ssh_client, command)

        # Avvia il thread
        thread = threading.Thread(target=run_tcpdump)
        thread.start()

        thread2 = threading.Thread(target=periodic_sync, args=(settings, self.name))
        thread2.start()

        return {"apposto": "cari ragazzi"}



@project_blueprint.route('/start-dump/<project_name>')
def start_dump(project_name):
    project = Project.load(project_name)
    project.analyze_pcap(f"./projects/{project_name}")
    return project.start_tcp_dump()


@project_blueprint.route('/create/<name>')
def create_project(name):
    Project(name)
    return jsonify({'message': 'Project created', 'name': name}), 200


@project_blueprint.route('/get-project/<name>', methods=['GET'])
def get_project(name):
    project = Project.load(name)
    if project:
        return jsonify(project.toJSON()), 200
    else:
        return jsonify({'message': 'Project not found'}), 404


@project_blueprint.route('/upload-pcap/<project_name>', methods=['POST'])
def upload_pcap(project_name):
    file = request.files['pcap_file']
    filename = secure_filename(file.filename)
    project = Project.load(project_name)
    if project:
        file_path = os.path.join(project.project_dir, filename)
        file.save(file_path)
        project.add_pcap(filename)
        return jsonify({'message': 'File uploaded and analyzed'}), 200
    else:
        return jsonify({'message': 'Project not found'}), 404


@project_blueprint.route('/list', methods=['GET'])
def list_projects():
    try:
        projects = [name for name in os.listdir(PCAP_DIR) if os.path.isdir(os.path.join(PCAP_DIR, name))]
        return jsonify(projects), 200
    except Exception as e:
        print(e)
        return jsonify([]), 200



@project_blueprint.route('/analyze/<project_name>/<pcap_name>/')
def analyze(project_name, pcap_name):
    project = Project.load(project_name)
    if project:
        project.analyze_pcap(f"{PCAP_DIR}/{project_name}/{pcap_name}.pcap")
        return jsonify({'message': 'File analyzed'}), 200


@project_blueprint.route('/set-port', methods=['POST'])
def set_port():
    if request.is_json:
        data = request.get_json()
        project = Project.load(data['project_name'])
        port = data['port']
        project.set_port(port)
        return jsonify({"saved": port}), 200
    else:
        return jsonify({"error": "Request must be JSON", "statusText": "erroree"}), 400


@project_blueprint.route('/start-watch/<project_name>')
def start_watch(project_name):
    project = Project.load(project_name)
    if project is not None:
        from watcher import active_observers
        from socketManager import socketio
        if project.name not in active_observers:
            watcher = Watcher(project, socketio)
            watcher.start_watching()
            return jsonify({'message': 'Watching started for project ' + project_name}), 200
        else:
            return jsonify({'message': 'Project \'' + project_name + '\' is already watching.'}), 200
    else:
        print("progetto non trovato")
        return jsonify({'message': 'Not project found with name: ' + project_name}), 404


@project_blueprint.route('/stop-watch/<project_name>')
def stop_watch(project_name):
    if project_name in active_observers:
        active_observers[project_name].stop_watching()
        return jsonify({'message': 'Watching stopped for project ' + project_name}), 200
    else:
        return jsonify({'message': 'Not watching project ' + project_name}), 400


@project_blueprint.route('/conversations')
def get_conversations():
    conversations_collection = get_db().conversations
    project_name = request.args.get('project_name')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 25))
    offset = (page - 1) * limit

    cursor = conversations_collection.find({"project_name": project_name}).sort("timestamp", DESCENDING).skip(offset).limit(limit)
    results = list(cursor)

    return json.loads(json_util.dumps(results))


@project_blueprint.route('/')
def test():
    return "test"
