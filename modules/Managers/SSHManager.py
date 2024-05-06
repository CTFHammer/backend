import os
import threading
import paramiko
from scp import SCPClient

from modules.database import save_settings
from celery import shared_task
from paramiko.ssh_exception import AuthenticationException, NoValidConnectionsError
from werkzeug.local import LocalProxy
from modules.database import get_db, load_settings
from modules.socketManager import socketio


@shared_task()
def connect_to_ssh():
    try:
        settings = load_settings()
    except ValueError as e:
        print("Error loading settings:", str(e))
        return False

    socketio.emit("debug", {"project_name": "avviata"}, to=None)

    required_keys = {"vulIp", "vulPort", "vulUser", "vulPass"}
    if all(key in settings for key in required_keys):
        print("posso provare")
        try:
            client = create_ssh_client(settings['vulIp'], settings['vulPort'], settings['vulUser'], settings['vulPass'])
            res = check_ssh_connection(client)
            client.close()
            return res
        except AuthenticationException as e:
            return "Wrong credential"
    else:
        print("Settings incomplete")
        return False


def create_ssh_client(server, port, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client


def check_ssh_connection(client):
    try:
        output, _ = execute_command(client, 'echo "SSH connection is alive"')
        return "SSH connection is alive" in output.decode("utf-8")
    except Exception as e:
        print(f"SSH connection check failed: {str(e)}")
        return False


def check_docker_presence(client):
    try:
        output, _ = execute_command(client, "docker --version")
        return "Docker version" in output.decode("utf-8")
    except Exception as e:
        print(f"Docker presence check failed: {str(e)}")
        return False


def execute_command(client, command):
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    return stdout.read(), stderr.read()


def execute_background_command(client, command):
    modified_command = f"nohup {command} > /tmp/{command.split()[0]}.log 2>&1 & echo $!"
    stdin, stdout, stderr = client.exec_command(modified_command)
    pid = stdout.read().decode().strip()
    return pid


def after_save_setting(settings):
    client = None
    try:
        client = create_ssh_client(settings['vulIp'], settings['vulPort'], settings['vulUser'], settings['vulPass'])
        is_ssh_active = check_ssh_connection(client)
        is_ssh_docker_present = check_docker_presence(client)
        update_settings = {"ssh_active": is_ssh_active, "ssh_docker_present": is_ssh_docker_present}
    except (NoValidConnectionsError, AuthenticationException) as e:
        update_settings = {"ssh_active": False, "ssh_docker_present": False}
    finally:
        if client:
            client.close()
    save_settings(update_settings)


def create_client_ssh(vul_ip: str, vul_port: int, vul_user: str, vul_pass: str) -> paramiko.SSHClient or False:
    try:
        return create_ssh_client(vul_ip, vul_port, vul_user, vul_pass)
    except (NoValidConnectionsError, AuthenticationException) as e:
        return False


def test_ssh(vul_ip: str, vul_port: int, vul_user: str, vul_pass: str):
    client = create_client_ssh(vul_ip, vul_port, vul_user, vul_pass)
    if client is False:
        return False
    result = check_ssh_connection(client)
    client.close()
    return result


def ssh_form_settings():
    settings = load_settings()
    return create_ssh_client(settings['vulIp'], settings['vulPort'], settings['vulUser'], settings['vulPass'])


def load_form_settings(settings):
    return create_client_ssh(settings['vulIp'], settings['vulPort'], settings['vulUser'], settings['vulPass'])


def download_files_scp(client, remote_path, local_path):
    if not os.path.exists(local_path):
        os.makedirs(local_path)

    with SCPClient(client.get_transport()) as scp:
        scp.get(remote_path, local_path, recursive=True)
