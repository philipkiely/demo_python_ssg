import markdown
import os
import signal
import subprocess
import sys
import time
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import webbrowser

###################
# Build Functions #
###################

def build_article():
    # html = markdown.markdown(your_text_string)
    pass

def copy_assets():
    pass

def build_site():
    # mkdir dist but also wipe it
    pass

#######################
# File System Watcher #
#######################

class Watcher:

    def __init__(self, directory=".", handler=FileSystemEventHandler()):
        self.observer = Observer()
        self.handler = handler
        self.directory = directory

    def run(self):
        self.observer.schedule(
            self.handler, self.directory, recursive=True)
        self.observer.start()
        print("Watcher Running in {}/".format(self.directory))
        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
        self.observer.join()
        print("\nWatcher Terminated")


class BuildHandler(FileSystemEventHandler):

    def on_any_event(self, event):
        if event.is_directory:
            return
        if "/dist/" not in event.src_path:
            print("build")
        # Incremental builds (only build the single post affected)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: `python build.py --dev` or `python build.py --prod`")
        exit
    elif sys.argv[1] == "--prod":
        build_site()
        # Deploy
    elif sys.argv[1] == "--dev":
        print("Initializing Static Site Generator")
        src_watcher = Watcher(".", BuildHandler())
        build_site()
        server_proc = subprocess.Popen(["python", "-m", "http.server", "--directory", "dist"])
        webbrowser.open("http://127.0.0.1:8000")
        src_watcher.run()
        if server_proc.pid:
            os.kill(server_proc.pid, signal.SIGTERM)
        print("Static Site Generator Ended")
    else:
        print("Usage: `python build.py --dev` or `python build.py --prod`")
        exit
