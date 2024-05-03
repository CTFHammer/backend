import json

from bson import ObjectId
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import emit
import logging
from modules.Managers.SSHManager import SSHManager
from modules.database import load_settings, save_settings
from modules.socketManager import create_socketio
from project.project import project_blueprint


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super(CustomJSONEncoder, self).default(obj)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = create_socketio(app)
app.json_encoder = CustomJSONEncoder

if __name__ == '__main__':
    socketio.run(app)

app.register_blueprint(project_blueprint, url_prefix='/project')
CORS(app)


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
    return jsonify(settings)


@app.route("/test-vul-connection", methods=['POST'])
def test_vul_connection():
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    data = request.get_json()
    print(data)
    if SSHManager.test_connection(data["vulIp"], int(data["vulPort"]), data["vulPass"]):
        return {"status": 0, "message": "Connected"}, 200
    else:
        return jsonify({"status": 1, "message": "Not connected"}), 200


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
