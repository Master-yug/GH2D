from flask import Flask, render_template
import json
import os

app = Flask(__name__)

# Get absolute path to root project directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

REPO_CONFIG_FILE = os.path.join(BASE_DIR, "repo_config.json")
MONITOR_CACHE_FILE = os.path.join(BASE_DIR, "data", "monitor_cache.json")

def load_repo_config():
    if os.path.exists(REPO_CONFIG_FILE):
        with open(REPO_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def load_monitor_cache():
    if os.path.exists(MONITOR_CACHE_FILE):
        with open(MONITOR_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

@app.route("/")
def index():
    repos = load_repo_config()
    monitor_data = load_monitor_cache()
    print("📦 Repos Loaded:", repos)  # ✅ DEBUG
    return render_template("index.html", repos=repos, monitor_data=monitor_data)

if __name__ == "__main__":
    app.run(debug=True)
