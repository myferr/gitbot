import discord
from discord import app_commands
from discord.ext import commands
import httpx

COLOR_PURPLE = 0x9b59b6

class GistCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    gist_group = app_commands.Group(name="gist", description="Commands related to GitHub Gists.")

    @gist_group.command(name="info", description="Provides detailed information about a GitHub Gist.")
    @app_commands.describe(gist_id="The ID of the Gist.")
    async def gist_info(self, interaction: discord.Interaction, gist_id: str):
        await interaction.response.defer()
        headers = {"Accept": "application/vnd.github.v3+json"}
        async with httpx.AsyncClient() as client:
            url = f"https://api.github.com/gists/{gist_id}"
            try:
                r = await client.get(url, headers=headers)
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    await interaction.followup.send(f"Could not find Gist with ID `{gist_id}`.")
                else:
                    await interaction.followup.send(f"An error occurred while fetching the Gist: {e}")
                return
            except httpx.RequestError as e:
                await interaction.followup.send(f"An error occurred while making the request: {e}")
                return

            data = r.json()

            description = data.get("description", "No description provided.")
            owner = data["owner"]["login"] if "owner" in data and data["owner"] else "Anonymous"
            html_url = data["html_url"]
            created_at = data["created_at"]
            updated_at = data["updated_at"]
            files = data["files"]

            file_list = "\n".join([f"- `{filename}` ({file_data['language'] or 'Unknown'})" for filename, file_data in files.items()])
            if not file_list:
                file_list = "No files found."

            embed = discord.Embed(
                title=f"Gist: {gist_id}",
                url=html_url,
                description=description,
                color=COLOR_PURPLE
            )
            embed.add_field(name="Owner", value=owner, inline=True)
            embed.add_field(name="Created At", value=created_at, inline=True)
            embed.add_field(name="Last Updated", value=updated_at, inline=True)
            embed.add_field(name="Files", value=file_list, inline=False)
            
            await interaction.followup.send(embed=embed)

    @gist_group.command(name="content", description="Shows the content of a specific file within a GitHub Gist.")
    @app_commands.describe(gist_id="The ID of the Gist.", filename="The name of the file within the Gist (e.g., `my_script.py`).")
    async def gist_content(self, interaction: discord.Interaction, gist_id: str, filename: str):
        await interaction.response.defer()
        headers = {"Accept": "application/vnd.github.v3+json"}
        async with httpx.AsyncClient() as client:
            url = f"https://api.github.com/gists/{gist_id}"
            try:
                r = await client.get(url, headers=headers)
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    await interaction.followup.send(f"Could not find Gist with ID `{gist_id}`.")
                else:
                    await interaction.followup.send(f"An error occurred while fetching the Gist: {e}")
                return
            except httpx.RequestError as e:
                await interaction.followup.send(f"An error occurred while making the request: {e}")
                return

            data = r.json()
            files = data.get("files", {})

            if filename not in files:
                await interaction.followup.send(f"File `{filename}` not found in Gist `{gist_id}`. Available files: {', '.join(files.keys()) if files else 'None'}")
                return

            file_data = files[filename]
            raw_url = file_data["raw_url"]
            
            try:
                r_content = await client.get(raw_url)
                r_content.raise_for_status()
            except httpx.HTTPStatusError as e:
                await interaction.followup.send(f"An error occurred while fetching the file content: {e}")
                return
            except httpx.RequestError as e:
                await interaction.followup.send(f"An error occurred while making the request for file content: {e}")
                return

            content = r_content.text

            file_extension = filename.split('.')[-1]
            language_map = {
                "py": "python", "js": "javascript", "ts": "typescript", "html": "html",
                "css": "css", "json": "json", "md": "markdown", "java": "java",
                "c": "c", "cpp": "cpp", "go": "go", "rb": "ruby", "php": "php",
                "sh": "bash", "yml": "yaml", "yaml": "yaml", "xml": "xml",
                "sql": "sql", "swift": "swift", "kt": "kotlin", "rs": "rust"
            }
            lang = language_map.get(file_extension, "")

            if len(content) > 1900:
                content = content[:1900] + "\n... (truncated due to length)"

            embed = discord.Embed(
                title=f"Content of {filename} from Gist {gist_id}",
                description=f"``` {lang}\n{content}\n```",
                color=COLOR_PURPLE
            )
            embed.set_footer(text=f"Full file: {raw_url}")
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GistCommands(bot))