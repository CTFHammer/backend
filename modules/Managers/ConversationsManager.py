from bson import ObjectId

from modules.database import get_db


def load_conversations(project_name: str, n: int):
    db = get_db()
    conversations = db.conversations.find({"project_name": project_name}).sort("timestamp", -1).limit(n)
    return list(conversations)


def load_conversation(id_conv: str):
    db = get_db()
    conversation = db.conversations.find_one({'_id': ObjectId(id_conv)})
    return conversation


def delete_conversation(id_conv: str):
    db = get_db()
    db.conversations.delete_one({'_id': ObjectId(id_conv)})
    return True
