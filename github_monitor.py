#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 12:59:26 2025

@author: master-yug
"""

import aiohttp
from config import GITHUB_USERS, GITHUB_REPOS, GITHUB_TOKEN

headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

class GitHubMonitor:
    def __init__(self):
        self.session = None
        self.last_commits = {}
        self.last_followers = {}

    async def setup(self):
        self.session = aiohttp.ClientSession()
       # Check token
        if GITHUB_TOKEN:
            resp = await self.fetch_json("https://api.github.com/user")
            if not resp or "login" not in resp:
               print("❌ Invalid GitHub token. Monitoring may fail.")
 

    async def fetch_json(self, url):
     async with self.session.get(url, headers=headers) as resp:
        if resp.status != 200:
            print(f"⚠️ GitHub API error {resp.status} for {url}")
            return None
        return await resp.json()


    async def check_commits(self):
     updates = []
     for repo in GITHUB_REPOS:
         url = f"https://api.github.com/repos/{repo}/commits"
         commits = await self.fetch_json(url)
         if not commits or not isinstance(commits, list):
             print(f"⚠️ No commit data for {repo}")
             continue
         latest = commits[0]["sha"]
         if repo not in self.last_commits or self.last_commits[repo] != latest:
             self.last_commits[repo] = latest
             updates.append(f"🧪 New commit in **{repo}**: {commits[0]['commit']['message']}")
     return updates

    async def check_followers(self):
     updates = []
     for user in GITHUB_USERS:
         url = f"https://api.github.com/users/{user}"
         data = await self.fetch_json(url)
         if not data or not isinstance(data, dict):
             print(f"⚠️ No user data for {user}")
             continue
         current_followers = data["followers"]
         prev = self.last_followers.get(user, current_followers)
         if current_followers > prev:
             updates.append(f"👤 **{user}** gained a new follower! Total: {current_followers}")
         self.last_followers[user] = current_followers
     return updates


    async def close(self):
        if self.session:
            await self.session.close()
