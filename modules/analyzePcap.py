import datetime
import subprocess

from bson import ObjectId
from celery import shared_task
from pymongo import DESCENDING
from modules.database import get_db
from modules.socketManager import socketio, emit_message


def get_conversations(filepath, filter_tcp):
    conversations = []
    command = f"tshark -r {filepath} -Y \"{filter_tcp}\" -T fields -e tcp.stream | sort -urn"
    result = subprocess.run(command, capture_output=True, text=True, shell=True)

    for line in result.stdout.splitlines():
        conversations.append(line)
    return conversations


def get_tcp_streams(filepath, stream_id, filter):
    command = f"tshark -r {filepath} -Y\"{filter}\" -q -z 'follow,tcp,raw,{stream_id}'"
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        return parse_conversation(result.stdout)
    else:
        print(f"Errore nel seguire il flusso TCP {stream_id}:", result.stderr)
        return None


def parse_conversation(conversation):
    messages = []
    lines = conversation.splitlines()
    for line in lines[6:-1]:
        sender = 'server' if line.startswith("\t") else 'client'
        messages.append({'sender': sender, 'message': line.strip()})

    return messages


@shared_task()
def analyze_conversation(filepath: str, project_name: str, port: int, max_conversations=100):
    db = get_db()
    conversations_collection = db.conversations
    conversations_collection.create_index([("timestamp", DESCENDING)])
    filter_packets = f"tcp.port != 443 && tcp.port != 22 && tcp.payload && tcp.port eq {port}"
    if port is None or port == -1:
        filter_packets = f"tcp.port != 443 && tcp.port != 22 && tcp.payload"
    conversations = get_conversations(filepath, filter_packets)
    new_conversations = []
    for x, conversation in enumerate(conversations):
        if x > max_conversations: break
        message = get_tcp_streams(filepath, conversation, filter_packets)
        new_conversations.append({
            "message": message,
            "project_name": project_name,
            "timestamp": datetime.datetime.now().isoformat(),
        })
    if len(conversations) > 0:
        conversations_collection.insert_many(new_conversations)
        parsed_conversations = [{k: str(v) if isinstance(v, ObjectId) else v for k, v in conv.items()} for conv in
                                new_conversations]
        emit_message("new_conversations", {
            "project_name": project_name,
            "conversations": len(new_conversations)
        })
        return parsed_conversations
    return []
