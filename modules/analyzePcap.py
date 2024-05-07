from datetime import datetime
import os
import subprocess
import re
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


def get_tcp_streams(filepath, stream_id, filter, regex_flag):
    command = f"tshark -r {filepath} -Y\"{filter}\" -q -z 'follow,tcp,raw,{stream_id}'"
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        return parse_conversation(result.stdout, regex_flag)
    else:
        print(f"Errore nel seguire il flusso TCP {stream_id}:", result.stderr)
        return None, None


def hex_to_ascii(hex_string):
    try:
        bytes_object = bytes.fromhex(hex_string)
        ascii_string = bytes_object.decode('ascii')
        return ascii_string, True
    except ValueError:
        return hex_string, False


def is_hex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


def parse_conversation(conversation, regex_pattern):
    messages = []
    lines = conversation.splitlines()
    conversation_tag = None
    regex_compiled = re.compile(regex_pattern)

    for line in lines[6:-1]:
        sender = 'server' if line.startswith("\t") else 'client'
        original_line = line.strip()

        line_content, converted = hex_to_ascii(original_line)
        format_type = 'hex' if not converted else 'ascii'

        if not conversation_tag and regex_compiled.search(line_content):
            conversation_tag = 'FlagIn' if sender == 'client' else 'FlagOut'

        messages.append({
            'sender': sender,
            'message': line_content,
            'format': format_type,
            'converted': converted,
        })

    return messages, conversation_tag


@shared_task(ignore_result=True)
def analyze_conversation(filepath: str, project_name: str, port: int, regex_flag: str, max_conversations=100,
                         delete=True):
    if not os.path.exists(filepath):
        return []
    db = get_db()
    conversations_collection = create_index(db)

    filter_packets = construct_filter(port)
    conversations = get_conversations(filepath, filter_packets)

    if conversations:
        new_conversations = process_conversations(conversations, max_conversations, filepath, filter_packets,
                                                  regex_flag, project_name)
        conversations_collection.insert_many(new_conversations)
        emit_new_conversation_message(project_name, new_conversations)
        cleanup(filepath, delete)
        print(new_conversations)
        return format_conversations_for_return(new_conversations)

    cleanup(filepath, delete)
    return []


def create_index(db):
    conversations_collection = db.conversations
    conversations_collection.create_index([("timestamp", DESCENDING)])
    conversations_collection.create_index([('project_name', 1), ('tag_flag', 1)])
    return conversations_collection


def construct_filter(port):
    if port is None or port == -1:
        return "tcp.payload"
    return f"tcp.payload && tcp.port eq {port}"


def process_conversations(conversations, max_conversations, filepath, filter_packets, regex_flag, project_name):
    new_conversations = []
    for i, conversation in enumerate(conversations):
        if i >= max_conversations:
            break
        message, tag = get_tcp_streams(filepath, conversation, filter_packets, regex_flag)
        new_conversations.append({
            "message": message,
            "project_name": project_name,
            "timestamp": datetime.now().isoformat(),
            "flag_tag": tag
        })
    return new_conversations


def emit_new_conversation_message(project_name, new_conversations):
    emit_message("new_conversations", {
        "project_name": project_name,
        "conversations": len(new_conversations)
    })


def cleanup(filepath, delete):
    if delete:
        os.remove(filepath)


def format_conversations_for_return(new_conversations):
    return [{k: str(v) if isinstance(v, ObjectId) else v for k, v in conv.items()} for conv in new_conversations]
