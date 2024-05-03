import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import emit
import logging
from modules.database import load_settings, save_settings
from modules.socketManager import create_socketio
from project.project import project_blueprint

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = create_socketio(app)

if __name__ == '__main__':
    socketio.run(app)


app.register_blueprint(project_blueprint, url_prefix='/project')
CORS(app)

SETTINGS_FILE = 'settings.json'



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
        save_settings(data)
        return jsonify({"saved": data}), 200
    else:
        return jsonify({"error": "Request must be JSON"}), 400


@app.route("/docker/list")
def list_docker():
    return ["lol"]
    # TODO add the real docker from the vulbox this will be the code in vulBox
    # list_containers = []
    # for container in client.containers.list():
    #     list_containers.append({"id": container.id, "name": container.name, "networks": container.ports})
    # return list_containers


logging.getLogger('werkzeug').setLevel(logging.WARN)


if __name__ == '__main__':
    socketio.run(debug=True)
