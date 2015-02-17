#Embedded file name: fsdlite\monitor.py
"""
Uses the watchdog module to monitor for filesystem changes and emits
an event whenever something is created, modified or delete in the
target directory. If the watchdog module is not available, the method
falls back to not monitoring at all.
"""
import os
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    class FileHandler(FileSystemEventHandler):

        def __init__(self, callback):
            self.callback = callback

        def on_any_event(self, event):
            if not event.is_directory:
                self.callback(event.event_type, event.src_path)


    def start_file_monitor(path, callback):
        if os.path.exists(path):
            handler = FileHandler(callback)
            observer = Observer()
            observer.schedule(handler, path, recursive=True)
            observer.start()
            return observer


    def stop_file_monitor(observer):
        if observer:
            observer.stop()
            observer.join()


except ImportError:

    def start_file_monitor(path, callback):
        return None


    def stop_file_monitor(observer):
        pass
