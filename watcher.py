import os
import threading

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


active_observers = {}


class Watcher(FileSystemEventHandler):

    def __init__(self, project, socketio):
        self.project = project
        self.socketio = socketio

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.pcap'):
            print(f"Detected new pcap file: {event.src_path}")
            filename = os.path.basename(event.src_path)
            self.project.add_pcap(filename)

            if self.socketio is not None:
                self.socketio.emit('new_pcap', {'message': 'New pcap file analyzed: ' + filename},  to=None)
            else:
                print("Error: socketio is not initialized.")


    def start_watching(self):
        if self.project.name not in active_observers:
            event_handler = self
            observer = Observer()
            observer.schedule(event_handler, path=self.project.project_dir, recursive=False)
            observer.start()
            active_observers[self.project.name] = observer
            thread = threading.Thread(target=observer.join)
            thread.start()
            print(f"Started watching project: {self.project.name}")


    def start_tcp_watching(self):
        pass


    def stop_watching(self):
        project_name = self.project.name
        if project_name in active_observers:
            observer = active_observers[project_name]
            observer.stop()
            observer.join()
            del active_observers[project_name]
            print(f"Stopped watching project: {project_name}")
