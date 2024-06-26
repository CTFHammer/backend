import json

from bson import ObjectId, json_util
from flask import Blueprint, jsonify
from flask_cors import CORS
from modules.Managers.ConversationsManager import load_conversations, load_conversation, delete_conversation


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super(CustomJSONEncoder, self).default(obj)


def conversations(project_name):
    return jsonify({"status": "ok", conversations: load_conversations(project_name, 10)})


conversations_blueprint = Blueprint('conversations', __name__)
CORS(conversations_blueprint)

conversations_blueprint.json_encoder = CustomJSONEncoder


def parse_json(data):
    return json.loads(json_util.dumps(data))


@conversations_blueprint.route("/get-first/<project_name>", methods=['GET'])
def conversations(project_name):
    conv = load_conversations(project_name, 10)
    return jsonify(parse_json(conv))


@conversations_blueprint.route("/<conversation_id>", methods=['GET'])
def single_conv(conversation_id):
    conv = load_conversation(conversation_id)
    return jsonify(parse_json(conv))


@conversations_blueprint.route("/<conversation_id>", methods=['DELETE'])
def del_conv(conversation_id):
    conv = delete_conversation(conversation_id)
    return {"result": conv}
