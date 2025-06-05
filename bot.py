import discord
from discord.ext import tasks
import aiohttp
import asyncio

from github_monitor import GitHubMonitor
from config import DISCORD_TOKEN, REPO_CHANNELS

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Bot is ready as {client.user}")
    check_updates.start()

@tasks.loop(minutes=2)
async def check_updates():
    commit_updates = await monitor.check_commits()
    follower_updates = await monitor.check_followers()

    for update in commit_updates:
        channel_id = REPO_CHANNELS.get(update["repo"])
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
        for channel_id in REPO_CHANNELS.values():
            channel = client.get_channel(channel_id)
            if channel:
                await channel.send(
                    f"👤 `{update['user']}` now has **{update['followers']}** followers!"
                )

async def main():
    async with aiohttp.ClientSession() as session:
        global monitor
        monitor = GitHubMonitor(session)
        async with client:
            await client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
