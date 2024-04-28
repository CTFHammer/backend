import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import emit
import logging
from config import create_app, create_docker_client
from db import get_db
from project.project import project_blueprint

app, socketio = create_app()
client = create_docker_client()



app.register_blueprint(project_blueprint, url_prefix='/project')

SETTINGS_FILE = 'settings.json'


def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)


def load_settings():
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        return {}


@socketio.on('connect')
def test_connect():
    emit('response', {'message': 'Connected'})


@socketio.on('message')
def test_message(data):
    emit('response', {'message': "ciao"})


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')


@app.route('/')
def saluta():
    return "Ciao"


@app.route('/settings', methods=['GET'])
def get_settings():
    settings = load_settings()
    regex_flag = settings.get('regexFlag', None)
    return jsonify({"regexFlag": regex_flag})


@app.route('/settings', methods=['POST'])
def set_settings():
    if request.is_json:
        data = request.get_json()
        settings = load_settings()
        settings['regexFlag'] = data.get("regexFlag")
        save_settings(settings)
        return jsonify({"saved": settings}), 200
    else:
        return jsonify({"error": "Request must be JSON"}), 400


@app.route("/docker/list")
def list_docker():
    # TODO add the real docker from the vulbox this will be the code in vulBox
    list_containers = []
    for container in client.containers.list():
        list_containers.append({"id": container.id, "name": container.name, "networks": container.ports})
    return list_containers


logging.getLogger('werkzeug').setLevel(logging.WARN)


if __name__ == '__main__':
    socketio.run(debug=True)
