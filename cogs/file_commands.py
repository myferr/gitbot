import discord
from discord import app_commands
from discord.ext import commands
import httpx

COLOR_PURPLE = 0x9b59b6

class FileCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="file", description="Shows the content of a file from a GitHub repository.")
    @app_commands.describe(repo="The repository in the format `owner/repo` (e.g., `myferr/x3`).", path="The path to the file (e.g., `cogs/leaderboard.py`).")
    async def file(self, interaction: discord.Interaction, repo: str, path: str):
        await interaction.response.defer()
        headers = {"Accept": "application/vnd.github.v3.raw"}
        async with httpx.AsyncClient() as client:
            url = f"https://api.github.com/repos/{repo}/contents/{path}"
            try:
                r = await client.get(url, headers=headers)
                r.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    await interaction.followup.send(f"Could not find file `{path}` in repository `{repo}`. Please check the repository and file path.")
                else:
                    await interaction.followup.send(f"An error occurred while fetching the file: {e}")
                return
            except httpx.RequestError as e:
                await interaction.followup.send(f"An error occurred while making the request: {e}")
                return

            content = r.text
            
            # Determine language for syntax highlighting
            file_extension = path.split('.')[-1]
            language_map = {
                "py": "python", "js": "javascript", "ts": "typescript", "html": "html",
                "css": "css", "json": "json", "md": "markdown", "java": "java",
                "c": "c", "cpp": "cpp", "go": "go", "rb": "ruby", "php": "php",
                "sh": "bash", "yml": "yaml", "yaml": "yaml", "xml": "xml",
                "sql": "sql", "swift": "swift", "kt": "kotlin", "rs": "rust"
            }
            lang = language_map.get(file_extension, "")

            lines = content.splitlines()
            if len(lines) > 45:
                content = "\n".join(lines[:45]) + "\n..."
            
            file_url = f"https://github.com/{repo}/blob/main/{path}"
            
            embed = discord.Embed(
                title=f"Content of {path} in {repo}",
                description=f"```{lang}\n{content}\n```",
                color=COLOR_PURPLE
            )
            embed.add_field(name="View Full File", value=f"[Click Here]({file_url})", inline=False)
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(FileCommands(bot))