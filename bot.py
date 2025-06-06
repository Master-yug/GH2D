import discord
from discord.ext import tasks
import asyncio
import aiohttp
import json
import os
from discord import app_commands

from github_monitor import GitHubMonitor
from config import DISCORD_TOKEN, ADMIN_IDS

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

REPOS_FILE = "repos.json"

def load_repos():
    if not os.path.exists(REPOS_FILE):
        return {}
    with open(REPOS_FILE, "r") as f:
        return json.load(f)

def save_repos(repos):
    with open(REPOS_FILE, "w") as f:
        json.dump(repos, f, indent=2)

repos = load_repos()

@client.event
async def on_ready():
    print(f"✅ Bot is ready as {client.user}")
    await tree.sync()
    check_updates.start()

@tasks.loop(minutes=2)
async def check_updates():
    commit_updates = await monitor.check_commits(repos)
    follower_updates = await monitor.check_followers()

    for update in commit_updates:
        channel_id = repos.get(update["repo"])
        if not channel_id:
            continue
        channel = client.get_channel(channel_id)
        if not channel:
            continue
        embed = discord.Embed(
            title=f"📝 New Commit in {update['repo']}",
            description=update["message"],
            url=update["url"],
            color=0x2ecc71
        )
        embed.set_footer(text=f"Author: {update['author']}")
        await channel.send(embed=embed)

    for update in follower_updates:
        for channel_id in repos.values():
            channel = client.get_channel(channel_id)
            if channel:
                await channel.send(
                    f"👤 `{update['user']}` now has **{update['followers']}** followers!"
                )

@tree.command(name="addrepo", description="Add a GitHub repository to monitor")
@app_commands.describe(repo="Format: owner/repo", channel="Channel to send updates")
async def addrepo(interaction: discord.Interaction, repo: str, channel: discord.TextChannel):
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("❌ You are not authorized to use this command.", ephemeral=True)
        return

    repos[repo] = channel.id
    save_repos(repos)
    await interaction.response.send_message(f"✅ Added `{repo}` to monitoring in {channel.mention}.")

@tree.command(name="removerepo", description="Remove a repository from monitoring")
@app_commands.describe(repo="Format: owner/repo")
async def removerepo(interaction: discord.Interaction, repo: str):
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("❌ You are not authorized to use this command.", ephemeral=True)
        return

    if repo in repos:
        del repos[repo]
        save_repos(repos)
        await interaction.response.send_message(f"🗑️ Removed `{repo}` from monitoring.")
    else:
        await interaction.response.send_message(f"⚠️ `{repo}` is not being monitored.")

async def main():
    async with aiohttp.ClientSession() as session:
        global monitor
        monitor = GitHubMonitor(session)
        async with client:
            await client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
