import discord
from discord import app_commands
from discord.ext import commands
import httpx
from datetime import datetime

COLOR_PURPLE = 0x9b59b6

class ReleaseInfoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="release", description="Shows information about a specific release of a GitHub repository.")
    @app_commands.describe(repo="The repository in the format `owner/repo` (e.g., `myferr/x3`).", tag="The tag of the release (e.g., `v1.0.0`).")
    async def release(self, interaction: discord.Interaction, repo: str, tag: str):
        await interaction.response.defer()
        headers = {"Accept": "application/vnd.github.v3+json"}
        async with httpx.AsyncClient() as client:
            url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
            try:
                r = await client.get(url, headers=headers)
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    await interaction.followup.send(f"Could not find release with tag `{tag}` for repository `{repo}`.")
                else:
                    await interaction.followup.send(f"An error occurred while fetching the release: {e}")
                return
            except httpx.RequestError as e:
                await interaction.followup.send(f"An error occurred while making the request: {e}")
                return

            data = r.json()

            release_name = data.get("name", data.get("tag_name", "N/A"))
            release_author = data["author"]["login"]
            release_date = datetime.strptime(data["published_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S UTC")
            release_url = data["html_url"]
            release_body = data.get("body", "No description provided.")
            
            embed = discord.Embed(
                title=f"Release: {release_name} for {repo}",
                url=release_url,
                description=release_body[:200] + "..." if len(release_body) > 200 else release_body,
                color=COLOR_PURPLE
            )
            embed.add_field(name="Tag", value=data["tag_name"], inline=True)
            embed.add_field(name="Author", value=release_author, inline=True)
            embed.add_field(name="Published At", value=release_date, inline=False)

            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ReleaseInfoCommand(bot))
