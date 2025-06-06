import aiohttp
import json
import os
from datetime import datetime

class GitHubMonitor:
    def __init__(self, session, github_token=None):
        self.session = session
        self.github_token = github_token
        self.cache_file = "data/monitor_cache.json"
        self.cache = self.load_cache()

    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                return json.load(f)
        return {}

    def save_cache(self):
        os.makedirs("data", exist_ok=True)
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f, indent=4)

    async def fetch_json(self, url):
        headers = {
            "Accept": "application/vnd.github+json"
        }
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"

        async with self.session.get(url, headers=headers) as response:
            return await response.json()

    async def check_commits(self, repo_channels):
        updates = []

        for repo in repo_channels:
            url = f"https://api.github.com/repos/{repo}/commits"
            data = await self.fetch_json(url)

            if isinstance(data, list) and data:
                latest_commit = data[0]
                sha = latest_commit["sha"]
                cached_sha = self.cache.get(repo, {}).get("last_sha")

                if sha != cached_sha:
                    message = latest_commit["commit"]["message"]
                    author = latest_commit["commit"]["author"]["name"]
                    commit_url = latest_commit["html_url"]

                    self.cache[repo] = {
                        "last_sha": sha,
                        "last_commit": message,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }

                    updates.append({
                        "repo": repo,
                        "message": message,
                        "author": author,
                        "url": commit_url
                    })

        self.save_cache()
        return updates

    async def check_followers(self, usernames=[]):
        updates = []

        if "profiles" not in self.cache:
            self.cache["profiles"] = {}

        for user in usernames:
            url = f"https://api.github.com/users/{user}"
            data = await self.fetch_json(url)

            if "followers" in data:
                followers = data["followers"]
                cached = self.cache["profiles"].get(user, {}).get("followers")

                if cached != followers:
                    self.cache["profiles"][user] = {
                        "followers": followers
                    }
                    updates.append({
                        "user": user,
                        "followers": followers
                    })

        self.save_cache()
        return updates
