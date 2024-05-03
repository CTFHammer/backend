import threading
import paramiko


class SSHManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.client = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(SSHManager, cls).__new__(cls)
        return cls._instance

    def initialize(self, server, port, user, password):
        if not hasattr(self, 'client'):
            self.client = self.create_ssh_client(server, port, user, password)

    @staticmethod
    def create_ssh_client(server, port, user, password):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(server, port, user, password)
            return client
        except Exception as e:
            print(f"Failed to connect: {str(e)}")
            raise Exception("Invalid SSH connection")

    def execute_command(self, command, background=False):
        if background:
            thread = threading.Thread(target=self._execute_command, args=(command,))
            thread.start()
            return thread
        else:
            return self._execute_command(command)

    @staticmethod
    def test_connection(host: str, port: int, password: str) -> bool:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, port, "root", password)
            client.exec_command('ls -l')
            return True
        except:
            return False

    def _execute_command(self, command):
        stdin, stdout, stderr = self.client.exec_command(command, get_pty=True)
        return stdout.read(), stderr.read()

    def close(self):
        self.client.close()
