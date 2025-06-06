from flask import Flask, render_template, request, redirect, url_for
import json
import os
import requests

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO_CONFIG_FILE = os.path.join(BASE_DIR, "repo_config.json")
MONITOR_CACHE_FILE = os.path.join(BASE_DIR, "data", "monitor_cache.json")

def load_repo_config():
    if os.path.exists(REPO_CONFIG_FILE):
        with open(REPO_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_repo_config(data):
    with open(REPO_CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_monitor_cache():
    if os.path.exists(MONITOR_CACHE_FILE):
        with open(MONITOR_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_monitor_cache(data):
    with open(MONITOR_CACHE_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/", methods=["GET"])
def index():
    repos = load_repo_config()
    monitor_data = load_monitor_cache()
    return render_template("index.html", repos=repos, monitor_data=monitor_data)

@app.route("/remove_repo", methods=["POST"])
def remove_repo():
    repo_to_remove = request.form.get("repo")
    if not repo_to_remove:
        return redirect(url_for("index"))

    # Remove from config
    repos = load_repo_config()
    if repo_to_remove in repos:
        del repos[repo_to_remove]
        save_repo_config(repos)

    # Remove from monitor cache
    monitor_data = load_monitor_cache()
    if repo_to_remove in monitor_data:
        del monitor_data[repo_to_remove]
        save_monitor_cache(monitor_data)

    return redirect(url_for("index"))

@app.route("/add_repo", methods=["POST"])
def add_repo():
    repo = request.form.get("repo")
    if not repo or "/" not in repo:
        return redirect(url_for("index"))

    # Load and update config
    repos = load_repo_config()
    if repo not in repos:
        # Default to channel ID 0 (you may want to update this later)
        repos[repo] = 0
        save_repo_config(repos)

    return redirect(url_for("index"))

@app.route("/add_profile", methods=["POST"])
def add_profile():
    username = request.form.get("username")
    if not username:
        return redirect(url_for("index"))

    url = f"https://api.github.com/users/{username}"
    headers = {"Accept": "application/vnd.github+json"}

    # If GITHUB_TOKEN is set in environment or config, include it
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            followers = data.get("followers", 0)

            cache = load_monitor_cache()
            if "profiles" not in cache:
                cache["profiles"] = {}
            cache["profiles"][username] = {"followers": followers}
            save_monitor_cache(cache)

    except Exception as e:
        print(f"[ERROR] Could not fetch GitHub user: {e}")

    return redirect(url_for("index"))


@app.route("/remove_profile", methods=["POST"])
def remove_profile():
    username = request.form.get("username")
    cache = load_monitor_cache()
    if "profiles" in cache and username in cache["profiles"]:
        del cache["profiles"][username]
        save_monitor_cache(cache)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)


