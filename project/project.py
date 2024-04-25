import os
import json
from threading import Thread
from flask import Blueprint, jsonify, request
from flask_socketio import emit
from werkzeug.utils import secure_filename

from socketManager import socketio

PCAP_DIR = './pcap'

# Creazione della Blueprint
project_blueprint = Blueprint('project', __name__)


class Project:
    def __init__(self, name):
        self.name = name
        self.project_dir = os.path.join(PCAP_DIR, name)
        if not os.path.exists(self.project_dir):
            os.makedirs(self.project_dir)
        self.pcap_files = []

    def add_pcap(self, pcap_file):
        filepath = os.path.join(self.project_dir, pcap_file)
        self.pcap_files.append(filepath)
        self.analyze_pcap(filepath)

    def analyze_pcap(self, filepath):
        print(f"Analyzing {filepath}")

    def save(self):
        project_data = {
            'name': self.name,
            'pcap_files': self.pcap_files,
        }
        with open(os.path.join(self.project_dir, 'project.json'), 'w') as f:
            json.dump(project_data, f)

    @staticmethod
    def load(project_name):
        project_path = os.path.join(PCAP_DIR, project_name, 'project.json')
        try:
            with open(project_path, 'r') as f:
                data = json.load(f)
                project = Project(data['name'])
                project.pcap_files = data['pcap_files']
                return project
        except (IOError, json.JSONDecodeError):
            return None


# Rotte specifiche della Blueprint
@project_blueprint.route('/create-project/<name>')
def create_project(name):
    print(name)
    project = Project(name)
    project.save()
    return jsonify({'message': 'Project created', 'name': name}), 200


@project_blueprint.route('/get-project/<name>', methods=['GET'])
def get_project(name):
    project = Project.load(name)
    if project:
        return jsonify({'name': project.name, 'pcap_files': project.pcap_files}), 200
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
        project.save()
        return jsonify({'message': 'File uploaded and analyzed'}), 200
    else:
        return jsonify({'message': 'Project not found'}), 404


@project_blueprint.route('/list-projects', methods=['GET'])
def list_projects():
    try:
        projects = [name for name in os.listdir(PCAP_DIR) if os.path.isdir(os.path.join(PCAP_DIR, name))]
        return jsonify({'projects': projects}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


observers = {}


@project_blueprint.route('/start-watch/<project_name>')
def start_watch(project_name):
    from watcher.watcher import start_watching  # Assume start_watching è una funzione definita nel modulo del progetto
    if project_name not in observers:
        observer_thread = Thread(target=start_watching, args=(project_name, socketio))
        observer_thread.start()
        observers[project_name] = observer_thread
        return jsonify({'message': 'Watching started for project ' + project_name}), 200
    else:
        return jsonify({'message': 'Already watching project ' + project_name}), 400


@project_blueprint.route('/stop-watch/<project_name>')
def stop_watch(project_name):
    if project_name in observers:
        observers[project_name].stop()
        observers.pop(project_name)
        return jsonify({'message': 'Watching stopped for project ' + project_name}), 200
    else:
        return jsonify({'message': 'Not watching project ' + project_name}), 400


@project_blueprint.route('/')
def test():
    return "test"
