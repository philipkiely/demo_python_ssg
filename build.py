import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
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

def parse_article_metadata(filename):
    f = open("src/posts/" + filename, "r")
    contents = f.readlines()
    f.close()
    parsed = {}
    parsed["title"] = contents[0].split(": ")[1]
    parsed["slug"] = contents[1].split(": ")[1]
    parsed["modified"] = datetime.datetime.strptime(
        contents[2].split(": ")[1][:-1], "%d-%m-%Y")
    parsed["cover"] = contents[3].split(": ")[1]
    parsed["content"] = markdown.markdown("".join(contents[4:]))
    return parsed

def generate_page(template, route, **kwargs):
    env = Environment(
        loader=FileSystemLoader(["theme/templates/"]),
        autoescape=select_autoescape(["html", "xml"]),
        auto_reload=True
    )
    html = env.get_template(template).render(kwargs)
    f = open("dist/{}.html".format(route), "w")
    f.write(html)
    f.close()

def build_article(article):
    generate_page(
        "post.html",
        article["slug"][:-1],
        article=article
    )

def build_index(articles):
    generate_page(
        "index.html",
        "index",
        articles=articles
    )

def copy_assets():
    if os.path.exists("dist/assets"):
        os.system("rm dist/assets/*")
    else:
        os.makedirs("dist/assets")
    os.system("cp -r src/assets dist/")
    os.system("cp -r theme/assets dist/")
    print("Assets Copied")

def build_site():
    if os.path.exists("dist"):
        os.system("rm dist/*")
    else:
        os.makedirs("dist")
    posts = subprocess.run(
        ["ls", "src/posts"],
        capture_output=True
    ).stdout.decode('utf-8').split('\n')
    posts = [p for p in posts if p != ""]
    articles = []
    for post in posts:
        articles.append(parse_article_metadata(post))
    articles.sort(key=lambda x: x["modified"], reverse=True)
    build_index(articles)
    for article in articles:
        build_article(article)
    copy_assets()

def build_article_incremental(article):
    if os.path.exists("dist/index.html"):
        os.system("rm dist/index.html")
    if os.path.exists("dist/{}".format(article)):
        os.system("rm dist/{}".format(article))
    posts = subprocess.run(
        ["ls", "src/posts"],
        capture_output=True
    ).stdout.decode('utf-8').split('\n')
    posts = [p for p in posts if p != ""]
    articles = []
    for post in posts:
        articles.append(parse_article_metadata(post))
    articles.sort(key=lambda x: x["modified"], reverse=True)
    build_index(articles)
    build_article([a for a in articles if a["slug"][:-1] == article[:-3]][0])
    print("Index & {} Updated".format(article))


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
            build_site()


class IncrementalBuildHandler(FileSystemEventHandler):

    def on_any_event(self, event):
        if event.is_directory:
            return
        if "/dist/" not in event.src_path:
            if "/assets/" in event.src_path:
                copy_assets()
            elif "/posts/" in event.src_path:
                build_article_incremental(event.src_path.split("/posts/")[1])
            else:
                build_site()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: `python build.py --dev` or `python build.py --prod`")
        exit
    elif sys.argv[1] == "--prod":
        build_site()
        print("Site ready to deploy from /dist/")
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
