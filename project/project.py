import json
import os
import pymongo
from bson import json_util
from flask import Blueprint, jsonify, request
from flask_cors import CORS
from pymongo import DESCENDING
from werkzeug.utils import secure_filename
from modules.Managers.ProjectManager import ProjectManager
from modules.Models.ProjectModel import Project
from modules.config import PCAP_DIR
from watcher import Watcher, active_observers

# Creazione della Blueprint
project_blueprint = Blueprint('project', __name__)
CORS(project_blueprint)

project_manager = ProjectManager()


@project_blueprint.route('/start-dump/<project_name>')
def start_dump(project_name):
    project = Project(project_name)
    project.pcap_manager.analyze_pcap(f"./collection/{project_name}")
    return project.start_tcp_dump()


@project_blueprint.route('/create/<name>')
def create_project(name):
    if project_manager.exists(name):
        return {"message": "Project already exists"}, 409
    else:
        project_manager.create_project_in_db(name)
        return jsonify({'message': 'Project created', 'name': name}), 201


@project_blueprint.route('/get-project/<name>', methods=['GET'])
def get_project(name):
    project_dic = project_manager.find_project(name)
    if project_dic is None:
        return {"message": "not found"}, 404
    else:
        return jsonify(Project.parse(project_dic)), 200


@project_blueprint.route('/upload-pcap/<project_name>', methods=['POST'])
def upload_pcap(project_name):
    file = request.files['pcap_file']
    filename = secure_filename(file.filename)
    project = Project(project_name)
    if project:
        file_path = os.path.join(project.project_dir, filename)
        file.save(file_path)
        project.add_pcap(filename)
        return jsonify({'message': 'File uploaded and analyzed'}), 200
    else:
        return jsonify({'message': 'Project not found'}), 404


@project_blueprint.route('/list')
def list_projects():
    return project_manager.list_projects()


@project_blueprint.route('/analyze/<project_name>/<pcap_name>/')
def analyze(project_name, pcap_name):
    project = Project(project_name)
    if project:
        project.pcap_manager.analyze_pcap(f"{PCAP_DIR}/{project_name}/{pcap_name}.pcap")
        return jsonify({'message': 'File analyzed'}), 200


@project_blueprint.route('/set-port', methods=['POST'])
def set_port():
    if request.is_json:
        data = request.get_json()
        print(data["project_name"], int(data["port"]))
        project_manager.set_port(data["project_name"], int(data["port"]))
        return {"saved": "success"}, 200
    else:
        print(request)
        return jsonify({"error": "Request must be JSON", "statusText": "erroree"}), 500


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


@project_blueprint.route("/delete/<project_name>")
def delete_project(project_name):
    if project_manager.exists(project_name) is False:
        return jsonify({'message': 'Project not found'}), 404
    project_manager.delete_project(project_name)
    project = Project(project_name)
    project.delete()
    return {"message": "Project deleted"}, 200


@project_blueprint.route('/conversations')
def get_conversations():
    conversations_collection = get_db().conversations
    project_name = request.args.get('project_name')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 25))
    offset = (page - 1) * limit

    cursor = conversations_collection.find({"project_name": project_name}).sort("timestamp", DESCENDING).skip(
        offset).limit(limit)
    results = list(cursor)

    return json.loads(json_util.dumps(results))


@project_blueprint.route('/')
def test():
    return "test"
