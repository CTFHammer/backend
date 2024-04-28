import datetime
import subprocess
import pyshark
from pymongo import ASCENDING, DESCENDING
import time
from db import get_db


db = get_db()
conversations_collection = db.conversations
conversations_collection.create_index([("timestamp", DESCENDING)])


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


def analyze_conversation(filepath, project_name, port, max_conversations=100):
    filter = f"tcp.port != 443 && tcp.port != 22 && tcp.payload && tcp.port eq {port}"
    if port is None or port == -1:
        filter = f"tcp.port != 443 && tcp.port != 22 && tcp.payload"
    conversations = get_conversations(filepath, filter)
    new_conversations = []
    for x, conversation in enumerate(conversations):
        if x > max_conversations: break
        message = get_tcp_streams(filepath, conversation, filter)
        new_conversations.append({
            "message": message,
            "project_name": project_name,
            "timestamp": datetime.datetime.now().isoformat(),
        })
    if len(conversations) > 0:
        conversations_collection.insert_many(new_conversations)
        return new_conversations


# a sort of brute force
# def save_tshark_output(filepath):
#     # Comando completo con pipe
#     command = f"tshark -r {filepath} -Y \"tcp.port != 443 && tcp.port != 22 && tcp.payload\" -T fields -e tcp.stream -E occurrence=f | uniq -c | awk '{{print $2, $1}}'"
#
#     # Esegui il comando utilizzando la shell
#     result = subprocess.run(command, capture_output=True, text=True, shell=True)
#     if result.returncode != 0:
#         print("Errore nell'esecuzione di tshark:", result.stderr)
#         return {}
#
#     # Processa l'output e salva i risultati
#     stream_counts = {}
#     output_lines = result.stdout.strip().split('\n')
#
#
#     for line in output_lines:
#         parts = line.split()
#         if len(parts) == 2:
#             stream_id, count = parts
#             stream_counts[stream_id] = int(count)
#
#     return stream_counts
#
#
# def analyze_conversation(filepath, project_name, max_conversations=100):
#     print(save_tshark_output(filepath))
#     return
#
#     project = projects_collection.find_one({'name': project_name})
#     print("start")
#     if not project:
#         project = {'name': project_name}
#         project['_id'] = projects_collection.insert_one(project).inserted_id
#
#     cap = pyshark.FileCapture(filepath, display_filter='tcp.port != 443 && tcp.port != 22 &&  tcp.payload', keep_packets=False)
#     stream_packets = {}
#     num_streams = set()
#
#     for packet in cap:
#         if 'TCP' in packet:
#             stream_id = packet.tcp.stream
#             if stream_id not in stream_packets:
#                 stream_packets[stream_id] = []
#             stream_packets[stream_id].append(packet)
#
#             if max_conversations < len(num_streams): break
#
#             if packet.tcp.flags_fin or packet.tcp.flags:
#                 # Processa e salva la conversazione per questo stream
#                 if stream_id in stream_packets:
#                     messages = reconstruct_tcp_stream(stream_packets[stream_id])
#                     if len(messages) == 0:
#                         del stream_packets[stream_id]
#                         continue
#                     last_packet_time = stream_packets[stream_id][-1].sniff_time
#                     new_conversation = {
#                         'project_id': project['_id'],
#                         'stream_id': stream_id,
#                         'messages': messages,
#                         'last_packet_time': last_packet_time
#                     }
#                     conversations_collection.insert_one(new_conversation)
#
#                     num_streams.add(stream_id)
#                     del stream_packets[stream_id]
#
#     cap.close()
#     print(f"Processed streams: {len(num_streams)}")
#     print("finito")
#
# def reconstruct_tcp_stream(packets):
#     messages = []
#     client_ip = packets[0].ip.src if packets else None
#
#     for packet in packets:
#         if hasattr(packet.tcp, 'payload'):
#             try:
#                 data_bytes = bytes.fromhex(packet.tcp.payload.replace(':', ''))
#                 message = data_bytes.decode('utf-8', errors='ignore')
#                 sender = 'client' if packet.ip.src == client_ip else 'server'
#                 messages.append({'sender': sender, 'message': message})
#             except Exception as e:
#                 print(f"Errore nella decodifica del pacchetto: {e}")
#
#     return messages
