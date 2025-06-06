import discord
from discord import app_commands
from discord.ext import tasks
import asyncio
import aiohttp
import json
import os

from github_monitor import GitHubMonitor
from config import DISCORD_TOKEN, GITHUB_TOKEN, ADMINS, REPO_CONFIG_FILE

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def load_repo_channels():
    if os.path.exists(REPO_CONFIG_FILE):
        with open(REPO_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_repo_channels(data):
    with open(REPO_CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {client.user}")
    check_updates.start()

@tasks.loop(minutes=2)
async def check_updates():
    repo_channels = load_repo_channels()
    commit_updates = await monitor.check_commits(repo_channels)
    follower_updates = await monitor.check_followers()

    for update in commit_updates:
        channel_id = repo_channels.get(update["repo"])
        if not channel_id:
            continue
        channel = client.get_channel(channel_id)
        if channel:
            embed = discord.Embed(
                title=f"📝 New Commit in {update['repo']}",
                description=update["message"],
                url=update["url"],
                color=0x2ecc71
            )
            embed.set_footer(text=f"Author: {update['author']}")
            await channel.send(embed=embed)

    for update in follower_updates:
        for channel_id in repo_channels.values():
            channel = client.get_channel(channel_id)
            if channel:
                await channel.send(
                    f"👤 `{update['user']}` now has **{update['followers']}** followers!"
                )

@tree.command(name="add_repo", description="Add a GitHub repository to monitor")
@app_commands.describe(repo="Format: owner/repo")
async def add_repo(interaction: discord.Interaction, repo: str):
    if interaction.user.id not in ADMINS:
        await interaction.response.send_message("🚫 You are not authorized to use this command.", ephemeral=True)
        return

    repo_channels = load_repo_channels()
    if repo in repo_channels:
        await interaction.response.send_message("🔁 Repository is already being monitored.", ephemeral=True)
    else:
        repo_channels[repo] = interaction.channel_id
        save_repo_channels(repo_channels)
        await interaction.response.send_message(f"✅ Now monitoring `{repo}` in this channel.")

async def main():
    async with aiohttp.ClientSession() as session:
        global monitor
        monitor = GitHubMonitor(session, GITHUB_TOKEN)
        async with client:
            await client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
