from flask_socketio import SocketIO

global socketio


def create_socketio(app):
    global socketio
    socketio = SocketIO(app, message_queue='amqp://', cors_allowed_origins="*")
    return socketio


def get_socketio() -> SocketIO:
    return socketio


def emit_message(subject: str, message):
    socketio.emit(subject, message, to=None)
