import discord
from discord import app_commands
from discord.ext import commands
import httpx
from datetime import datetime

COLOR_PURPLE = 0x9b59b6

class RepoCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="repo", description="Provides detailed information about a specified GitHub repository.")
    @app_commands.describe(repo="The repository in the format `owner/repo` (e.g., `myferr/x3`).")
    async def repo(self, interaction: discord.Interaction, repo: str):
        await interaction.response.defer()
        headers = {"Accept": "application/vnd.github.v3+json"}
        async with httpx.AsyncClient() as client:
            url = f"https://api.github.com/repos/{repo}"
            r = await client.get(url, headers=headers)
            if r.status_code != 200:
                await interaction.followup.send(f"Could not find repository `{repo}`")
                return
            data = r.json()

        name = data["name"]
        owner = data["owner"]["login"]
        description = data.get("description", "No description.")
        lang = data.get("language", "Unknown")
        stars = data.get("stargazers_count", 0)
        forks = data.get("forks_count", 0)
        updated = datetime.strptime(data["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
        updated_str = updated.strftime("%Y-%m-%d %H:%M:%S UTC")
        html_url = data["html_url"]

        embed = discord.Embed(
            title=f"{owner}/{name}",
            url=html_url,
            description=description,
            color=COLOR_PURPLE
        )
        embed.add_field(name="Owner", value=owner, inline=True)
        embed.add_field(name="Language", value=lang, inline=True)
        embed.add_field(name="Stars", value=str(stars), inline=True)
        embed.add_field(name="Forks", value=str(forks), inline=True)
        embed.add_field(name="Last Updated", value=updated_str, inline=False)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RepoCommands(bot))
