import discord
from discord import app_commands
from discord.ext import commands
import httpx

COLOR_ORANGE = 0xe67e22

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="Displays comprehensive information about a GitHub user.")
    @app_commands.describe(username="The GitHub username of the user you want to look up (e.g., octocat).")
    async def profile(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer()
        headers = {"Accept": "application/vnd.github.v3+json"}
        async with httpx.AsyncClient() as client:
            url = f"https://api.github.com/users/{username}"
            r = await client.get(url, headers=headers)
            if r.status_code != 200:
                await interaction.followup.send(f"Could not find GitHub user `{username}`")
                return
            data = r.json()

        name = data.get("name") or username
        login = data["login"]
        bio = data.get("bio", "No bio.")
        public_repos = data.get("public_repos", 0)
        html_url = data["html_url"]
        avatar_url = data["avatar_url"]

        embed = discord.Embed(
            title=f"{name}'s GitHub Profile",
            url=html_url,
            description=bio,
            color=COLOR_ORANGE
        )
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="Username", value=login, inline=True)
        embed.add_field(name="Public Repositories", value=str(public_repos), inline=True)
        embed.add_field(name="Profile", value=f"[{html_url}]({html_url})", inline=False)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Profile(bot))

