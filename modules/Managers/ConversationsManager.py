from bson import ObjectId

from modules.database import get_db


def load_conversations(n: int):
    db = get_db()
    conversations = db.conversations.find().limit(n)
    return list(conversations)


def load_conversation(id_conv: str):
    db = get_db()
    conversation = db.conversations.find_one({'_id': ObjectId(id_conv)})
    return conversation
