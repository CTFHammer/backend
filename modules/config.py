from flask import Flask
from celery import Celery, Task
from flask_pymongo import PyMongo

from modules.socketManager import create_socketio

PCAP_DIR = 'projects'
MONGO_URI = "mongodb://localhost:27017/CTFHammer"


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app_in = Celery(app.name, task_cls=FlaskTask)
    celery_app_in.config_from_object(app.config["CELERY"])
    celery_app_in.set_default()
    app.extensions["celery"] = celery_app_in
    return celery_app_in


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        CELERY=dict(
            broker_url="amqp://guest:guest@localhost/",
            result_backend=MONGO_URI,
        ),
    )
    app.config.from_prefixed_env()
    celery_init_app(app)
    return app


app = create_app()

app.config["MONGO_URI"] = MONGO_URI
app.config['SECRET_KEY'] = 'secret!'
socketio = create_socketio(app)
mongo = PyMongo(app)
