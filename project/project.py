import json
import os
from bson import json_util
from celery import current_app
from celery.worker.control import revoke
from flask import Blueprint, jsonify, request
from flask_cors import CORS
from pymongo import DESCENDING
from werkzeug.utils import secure_filename
from modules.Managers.ProjectManager import ProjectManager, start_tcp_dump, stop_tcp_dump, download_pcap, save_project, \
    find_project, stop_task, get_task_status
from modules.Models.ProjectModel import Project
from modules.analyzePcap import analyze_conversation
from modules.config import PCAP_DIR, app
from modules.Managers.ProjectManager import start_analysis
from modules.database import get_db

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
    project_dic = find_project(name)
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


@project_blueprint.route('/start-tcp-dump/<project_name>')
def start_watch(project_name):
    ris = start_tcp_dump(project_name)
    return ris, 200


@project_blueprint.route("/delete/<project_name>")
def delete_project(project_name):
    if project_manager.exists(project_name) is False:
        return jsonify({'message': 'Project not found'}), 404
    project_manager.delete_project(project_name)
    project = Project(project_name)
    project.delete()
    return {"message": "Project deleted"}, 200


@project_blueprint.route("/analyze-pcap/<project_name>")
def analyze_pcap(project_name):
    res = analyze_conversation.delay("./projects/prova/test.pcap",
                                     project_name,
                                     54321)
    return {"result": "Task started", "id": res.id}


@project_blueprint.route('/stop-tcp-dump/<project_name>')
def stop_tcp(project_name):
    return stop_tcp_dump(project_name), 200


@project_blueprint.route('/download-dump/<project_name>')
def download_tcp_dump(project_name):
    download_pcap(project_name)
    return {"message": "downloading"}


@project_blueprint.route('/start-total-dump/<project_name>')
def start_total_dump(project_name):
    start_tcp_dump(project_name)
    res = start_analysis.delay(project_name)
    save_project(project_name, {"task_total": res.id})
    return {"message": "Total dump started", "pid": res.id}, 200


@project_blueprint.route('/test-dump')
def test_dump():
    print(os.getcwd())
    analyze_conversation("./daje.pcap", "prova", 54321, "google", delete=False)
    return {"message": "Total dump started"}, 200


@project_blueprint.route('/stop-total-dump/<project_name>')
def stop_total_dump(project_name):
    project = find_project(project_name)
    stop_task(project["task_total"])
    save_project(project_name, {"task_total": ""})
    stop_tcp_dump(project_name)
    return {"message": "Total dump stopped"}, 200


@project_blueprint.route('/')
def test():
    return "test"
