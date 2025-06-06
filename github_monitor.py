import aiohttp
from config import GITHUB_TOKEN


class GitHubMonitor:
    def __init__(self, session):
        self.session = session
        self.last_commit_sha = {}
        self.last_followers = {}

    async def fetch_json(self, url):
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        async with self.session.get(url, headers=headers) as resp:
            if resp.status != 200:
                print(f"⚠️ GitHub API error {resp.status} for {url}")
                return None
            return await resp.json()

    async def check_commits(self, repos):
        updates = []
        for repo, channel_id in repos.items():
            url = f"https://api.github.com/repos/{repo}/commits"
            data = await self.fetch_json(url)
            if not data or not isinstance(data, list):
                print(f"⚠️ No commit data for {repo}")
                continue

            latest = data[0]["sha"]
            if repo not in self.last_commit_sha or self.last_commit_sha[repo] != latest:
                self.last_commit_sha[repo] = latest
                commit = data[0]
                updates.append({
                    "repo": repo,
                    "message": commit["commit"]["message"],
                    "url": commit["html_url"],
                    "author": commit["commit"]["author"]["name"]
                })
        return updates

    async def check_followers(self):
        updates = []
        for repo in self.last_commit_sha:
            user = repo.split("/")[0]
            url = f"https://api.github.com/users/{user}"
            data = await self.fetch_json(url)
            if not data or "followers" not in data:
                continue

            followers = data["followers"]
            if user not in self.last_followers or self.last_followers[user] != followers:
                self.last_followers[user] = followers
                updates.append({
                    "user": user,
                    "followers": followers
                })
        return updates
