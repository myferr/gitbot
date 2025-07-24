import discord
from discord import app_commands
from discord.ext import commands
import httpx
from datetime import datetime

COLOR_PURPLE = 0x9b59b6

class ReleasePaginator(discord.ui.View):
    def __init__(self, releases, repo_name):
        super().__init__(timeout=180)
        self.releases = releases
        self.repo_name = repo_name
        self.current_page = 0
        self.releases_per_page = 5

    def _get_page_content(self):
        start_index = self.current_page * self.releases_per_page
        end_index = start_index + self.releases_per_page
        return self.releases[start_index:end_index]

    def _create_embed(self):
        page_releases = self._get_page_content()
        embed = discord.Embed(
            title=f"Releases for {self.repo_name} (Page {self.current_page + 1}/{self.total_pages})",
            color=COLOR_PURPLE
        )
        if not page_releases:
            embed.description = "No releases found for this page."
            return embed

        for release in page_releases:
            release_name = release.get("name", release.get("tag_name", "N/A"))
            release_tag = release["tag_name"]
            release_date = datetime.strptime(release["published_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
            release_url = release["html_url"]
            embed.add_field(name=f"{release_name} ({release_tag})", value=f"Published: {release_date} | [View Release]({release_url})", inline=False)
        return embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, custom_id="previous_release_page")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self._create_embed(), view=self)
        else:
            await interaction.response.send_message("You are on the first page.", ephemeral=True)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, custom_id="next_release_page")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self._create_embed(), view=self)
        else:
            await interaction.response.send_message("You are on the last page.", ephemeral=True)

    @property
    def total_pages(self):
        return (len(self.releases) + self.releases_per_page - 1) // self.releases_per_page

class ReleasesCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="releases", description="Lists the latest releases of a GitHub repository with pagination.")
    @app_commands.describe(repo="The repository in the format `owner/repo` (e.g., `myferr/x3`).")
    async def releases(self, interaction: discord.Interaction, repo: str):
        await interaction.response.defer()
        headers = {"Accept": "application/vnd.github.v3+json"}
        all_releases = []
        page = 1
        while True:
            async with httpx.AsyncClient() as client:
                url = f"https://api.github.com/repos/{repo}/releases?per_page=100&page={page}"
                try:
                    r = await client.get(url, headers=headers)
                    r.raise_for_status()
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404 and page == 1:
                        await interaction.followup.send(f"Could not find releases for repository `{repo}`. It might not have any releases or the repository does not exist.")
                        return
                    elif e.response.status_code == 404: # No more pages
                        break
                    else:
                        await interaction.followup.send(f"An error occurred while fetching releases: {e}")
                        return
                except httpx.RequestError as e:
                    await interaction.followup.send(f"An error occurred while making the request: {e}")
                    return

                data = r.json()
                if not data:
                    break
                all_releases.extend(data)
                page += 1

        if not all_releases:
            await interaction.followup.send(f"No releases found for repository `{repo}`.")
            return

        view = ReleasePaginator(all_releases, repo)
        await interaction.followup.send(embed=view._create_embed(), view=view)

async def setup(bot):
    await bot.add_cog(ReleasesCommand(bot))
