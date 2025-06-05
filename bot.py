#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 13:01:25 2025

@author: master-yug
"""

import discord
from discord.ext import tasks
from config import DISCORD_TOKEN, DISCORD_CHANNEL_ID
from github_monitor import GitHubMonitor

intents = discord.Intents.default()
client = discord.Client(intents=intents)

monitor = GitHubMonitor()

@client.event
async def on_ready():
    print(f'Bot is ready as {client.user}')
    await monitor.setup()  # ✅ Create aiohttp session within the event loop
    check_updates.start()

@tasks.loop(minutes=5)
async def check_updates():
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    commit_updates = await monitor.check_commits()
    follower_updates = await monitor.check_followers()
    for update in commit_updates + follower_updates:
        await channel.send(update)

@client.event
async def on_disconnect():
    await monitor.close()

client.run(DISCORD_TOKEN)

