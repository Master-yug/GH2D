import aiohttp
import asyncio
from config import GITHUB_REPOS, GITHUB_USERS, GITHUB_TOKEN

API_BASE = "https://api.github.com"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

class GitHubMonitor:
    def __init__(self, session):
        self.session = session
        self.last_commit = {}
        self.last_followers = {}

    async def fetch_json(self, url):
        try:
            async with self.session.get(url.strip(), headers=HEADERS) as resp:
                if resp.status == 200:
                    return await resp.json()
                print(f"⚠️ GitHub API error {resp.status} for {url}")
                return None
        except Exception as e:
            print(f"❌ Exception fetching {url}: {e}")
            return None

    async def check_commits(self):
        updates = []
        for repo in GITHUB_REPOS:
            repo = repo.strip()
            url = f"{API_BASE}/repos/{repo}/commits"
            commits = await self.fetch_json(url)
            if not commits:
                print(f"⚠️ No commit data for {repo}")
                continue

            latest = commits[0].get("sha")
            if latest and self.last_commit.get(repo) != latest:
                self.last_commit[repo] = latest
                updates.append({
                    "repo": repo,
                    "message": commits[0]["commit"]["message"],
                    "author": commits[0]["commit"]["author"]["name"],
                    "url": commits[0]["html_url"]
                })
        return updates

    async def check_followers(self):
        updates = []
        for user in GITHUB_USERS:
            user = user.strip()
            url = f"{API_BASE}/users/{user}"
            data = await self.fetch_json(url)
            if not data:
                continue
            current_followers = data.get("followers")
            if current_followers is None:
                continue
            last = self.last_followers.get(user, current_followers)
            if current_followers != last:
                self.last_followers[user] = current_followers
                updates.append({
                    "user": user,
                    "followers": current_followers
                })
        return updates

