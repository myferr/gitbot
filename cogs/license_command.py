import discord
from discord import app_commands
from discord.ext import commands
import httpx

COLOR_PURPLE = 0x9b59b6

class LicenseCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="license", description="Shows the license information for a GitHub repository.")
    @app_commands.describe(repo="The repository in the format `owner/repo` (e.g., `myferr/x3`).")
    async def license(self, interaction: discord.Interaction, repo: str):
        await interaction.response.defer()
        headers = {"Accept": "application/vnd.github.v3+json"}
        async with httpx.AsyncClient() as client:
            url = f"https://api.github.com/repos/{repo}/license"
            try:
                r = await client.get(url, headers=headers)
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    await interaction.followup.send(f"Could not find license information for repository `{repo}`. It might not have an explicitly defined license.")
                else:
                    await interaction.followup.send(f"An error occurred while fetching the license: {e}")
                return
            except httpx.RequestError as e:
                await interaction.followup.send(f"An error occurred while making the request: {e}")
                return

            data = r.json()

            license_name = data.get("name", "N/A")
            license_type = data.get("spdx_id", "N/A")
            license_url = data.get("html_url", "N/A")
            
            embed = discord.Embed(
                title=f"License for {repo}",
                description=f"**License Name:** {license_name}\n**License Type:** {license_type}\n**License URL:** {license_url}",
                color=COLOR_PURPLE
            )
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LicenseCommand(bot))
