import discord
from discord import app_commands
from discord.ext import commands
import httpx
from datetime import datetime

COLOR_PURPLE = 0x9b59b6

class CommitInfoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="commit", description="Shows information about a specific commit in a GitHub repository.")
    @app_commands.describe(repo="The repository in the format `owner/repo` (e.g., `myferr/x3`).", sha="The SHA of the commit.")
    async def commit(self, interaction: discord.Interaction, repo: str, sha: str):
        await interaction.response.defer()
        headers = {"Accept": "application/vnd.github.v3+json"}
        async with httpx.AsyncClient() as client:
            url = f"https://api.github.com/repos/{repo}/commits/{sha}"
            try:
                r = await client.get(url, headers=headers)
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    await interaction.followup.send(f"Could not find commit with SHA `{sha}` for repository `{repo}`.")
                else:
                    await interaction.followup.send(f"An error occurred while fetching the commit: {e}")
                return
            except httpx.RequestError as e:
                await interaction.followup.send(f"An error occurred while making the request: {e}")
                return

            data = r.json()

            commit_message = data["commit"]["message"]
            commit_author = data["commit"]["author"]["name"]
            commit_date = datetime.strptime(data["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S UTC")
            commit_url = data["html_url"]
            
            embed = discord.Embed(
                title=f"Commit: {sha[:7]} for {repo}",
                url=commit_url,
                description=commit_message,
                color=COLOR_PURPLE
            )
            embed.add_field(name="Author", value=commit_author, inline=True)
            embed.add_field(name="Date", value=commit_date, inline=True)

            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CommitInfoCommand(bot))
