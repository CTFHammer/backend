import os
import subprocess
import threading
import paramiko
from scp import SCPClient
import time

BASE_DIR = os.getcwd()


def create_ssh_client(server, port, user="root", password="password"):
    """ Funzione per creare una connessione SSH al server remoto. """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client


def execute_remote_command(ssh_client, command):
    """ Esegui un comando sul server remoto. """
    stdin, stdout, stderr = ssh_client.exec_command(command, get_pty=True)
    return stdout.readlines(), stderr.readlines()


def copy_file_from_remote(ssh_client, remote_path, local_path):
    """ Copia un file dal server remoto al sistema locale. """
    with SCPClient(ssh_client.get_transport()) as scp:
        scp.get(remote_path, local_path)




def sync_dumps(remote_path, local_path, settings):
    port_part = f"-p {settings['port']}" if 'port' in settings and settings['port'] else ""
    command = f"sshpass -p '{settings['password']}' rsync -avz --remove-source-files -e 'ssh {port_part} -o StrictHostKeyChecking=no' root@localhost:{remote_path} {local_path}"

    def run_command():
        try:
            # Esegui il comando localmente
            result = subprocess.run(command, shell=True, text=True, capture_output=True, check=True)
            # Output positivo
            print("Success:", result.stdout)
        except subprocess.CalledProcessError as e:
            pass
        except Exception as e:
            # Altri errori generici
            print("Exception:", str(e))

    # Crea e avvia un thread per eseguire il comando
    thread = threading.Thread(target=run_command)
    thread.start()
    return {"apposto": "caro"}


def periodic_sync(settings, project_name, interval=10):
    # ssh_client = create_ssh_client(settings["server_vul"], settings["port_vul"], settings["user"], settings["password"])
    while True:
        local_dir = f"{BASE_DIR}/projects/{project_name}/"
        sync_dumps(f"/pcap/{project_name}/*.pcap", local_dir, settings)
        time.sleep(interval)
