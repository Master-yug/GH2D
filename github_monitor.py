# github_monitor.py

import aiohttp
import json

class GitHubMonitor:
    def __init__(self, session, github_token):
        self.session = session
        self.token = github_token
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.last_commit_shas = {}
        self.last_followers = {}

    async def check_commits(self, repo_channels):
        updates = []
        for repo in repo_channels:
            url = f"https://api.github.com/repos/{repo}/commits"
            async with self.session.get(url, headers=self.headers) as resp:
                if resp.status != 200:
                    print(f"GitHub API error {resp.status} for {url}")
                    continue
                data = await resp.json()
                if not data:
                    continue
                latest = data[0]
                sha = latest["sha"]
                if repo not in self.last_commit_shas or self.last_commit_shas[repo] != sha:
                    self.last_commit_shas[repo] = sha
                    updates.append({
                        "repo": repo,
                        "message": latest["commit"]["message"],
                        "url": latest["html_url"],
                        "author": latest["commit"]["author"]["name"]
                    })
        return updates

    async def check_followers(self):
        updates = []
        usernames = list({repo.split('/')[0] for repo in self.last_commit_shas.keys()})
        for username in usernames:
            url = f"https://api.github.com/users/{username}"
            async with self.session.get(url, headers=self.headers) as resp:
                if resp.status != 200:
                    continue
                data = await resp.json()
                followers = data.get("followers", 0)
                if username not in self.last_followers or self.last_followers[username] != followers:
                    self.last_followers[username] = followers
                    updates.append({
                        "user": username,
                        "followers": followers
                    })
        return updates
