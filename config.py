from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import docker

from socketManager import create_socketio


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    # CORS(app)  # Abilita il supporto per le credenziali se necessario
    socketio = create_socketio(app)
    return app, socketio


def create_docker_client():
    return docker.DockerClient(base_url='unix://var/run/docker.sock')
