from flask_socketio import SocketIO

global socketio

def create_socketio(app):
    global socketio
    socketio = SocketIO(app, cors_allowed_origins="*")
    return socketio

def get_socketio() -> SocketIO:
    return socketio
