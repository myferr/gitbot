import discord
from discord import app_commands
from discord.ext import commands
import httpx
from collections import Counter

COLOR_PURPLE = 0x9b59b6

class Top(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    top = app_commands.Group(name="top", description="Top GitHub info")

    @top.command(name="langs", description="Show top used languages for a user")
    @app_commands.describe(username="GitHub username")
    async def langs(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer()
        async with httpx.AsyncClient() as client:
            r = await client.get(f"https://api.github.com/users/{username}/repos")
            if r.status_code != 200:
                await interaction.followup.send(f"Could not find GitHub user `{username}`")
                return
            repos = r.json()

        langs = []
        for repo in repos:
            lang = repo.get("language")
            if lang:
                langs.append(lang)

        if not langs:
            await interaction.followup.send("No languages found.")
            return

        count = Counter(langs)
        total = sum(count.values())
        sorted_langs = count.most_common()

        desc = "\n".join(
            f"**{lang}**: {count} ({(count/total*100):.1f}%)"
            for lang, count in sorted_langs
        )

        embed = discord.Embed(
            title=f"Top Languages for {username}",
            description=desc,
            color=COLOR_PURPLE
        )

        await interaction.followup.send(embed=embed)

    @top.command(name="repos", description="Show a user's repositories sorted by stars")
    @app_commands.describe(username="GitHub username")
    async def repos(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer()
        async with httpx.AsyncClient() as client:
            r = await client.get(f"https://api.github.com/users/{username}/repos")
            if r.status_code != 200:
                await interaction.followup.send(f"Could not find GitHub user `{username}`")
                return
            repos = r.json()

        if not repos:
            await interaction.followup.send("No repositories found.")
            return

        sorted_repos = sorted(repos, key=lambda r: r["stargazers_count"], reverse=True)[:10]

        desc = "\n".join(
            f"⭐ {repo['stargazers_count']} — [{repo['name']}]({repo['html_url']})"
            for repo in sorted_repos
        )

        embed = discord.Embed(
            title=f"Top Repositories for {username}",
            description=desc,
            color=COLOR_PURPLE
        )

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Top(bot))

