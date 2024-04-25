import os

from watchdog import observers
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from project.project import Project


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
            self.project.save()
            self.socketio.emit('new_pcap', {'message': 'New pcap file analyzed: ' + filename})


def start_watching(project_name, socketio):
    project = Project.load(project_name)
    if project:
        event_handler = Watcher(project, socketio)
        observer = Observer()
        observer.schedule(event_handler, path=project.project_dir, recursive=False)
        observer.start()
        observers[project_name] = observer
        try:
            observer.join()
        except KeyboardInterrupt:
            observer.stop()
    else:
        print("Project not found!")
