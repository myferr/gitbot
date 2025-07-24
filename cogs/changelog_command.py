import discord
from discord import app_commands
from discord.ext import commands
import httpx
from datetime import datetime

COLOR_PURPLE = 0x9b59b6

class CommitPaginator(discord.ui.View):
    def __init__(self, commits, repo_name):
        super().__init__(timeout=180)
        self.commits = commits
        self.repo_name = repo_name
        self.current_page = 0
        self.commits_per_page = 5

    def _get_page_content(self):
        start_index = self.current_page * self.commits_per_page
        end_index = start_index + self.commits_per_page
        return self.commits[start_index:end_index]

    def _create_embed(self):
        page_commits = self._get_page_content()
        embed = discord.Embed(
            title=f"Commits for {self.repo_name} (Page {self.current_page + 1}/{self.total_pages})",
            color=COLOR_PURPLE
        )
        if not page_commits:
            embed.description = "No commits found for this page."
            return embed

        for commit in page_commits:
            commit_sha = commit["sha"][:7]
            commit_message = commit["commit"]["message"].splitlines()[0]
            commit_author = commit["commit"]["author"]["name"]
            commit_date = datetime.strptime(commit["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
            commit_url = commit["html_url"]
            embed.add_field(name=f"{commit_sha} by {commit_author}", value=f"{commit_message} ([View Commit]({commit_url})) on {commit_date}", inline=False)
        return embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, custom_id="previous_commit_page")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self._create_embed(), view=self)
        else:
            await interaction.response.send_message("You are on the first page.", ephemeral=True)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, custom_id="next_commit_page")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self._create_embed(), view=self)
        else:
            await interaction.response.send_message("You are on the last page.", ephemeral=True)

    @property
    def total_pages(self):
        return (len(self.commits) + self.commits_per_page - 1) // self.commits_per_page

class ChangelogCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="changelog", description="Lists recent commits (changelog) for a GitHub repository with pagination.")
    @app_commands.describe(repo="The repository in the format `owner/repo` (e.g., `myferr/x3`).")
    async def changelog(self, interaction: discord.Interaction, repo: str):
        await interaction.response.defer()
        headers = {"Accept": "application/vnd.github.v3+json"}
        all_commits = []
        page = 1
        while True:
            async with httpx.AsyncClient() as client:
                url = f"https://api.github.com/repos/{repo}/commits?per_page=100&page={page}"
                try:
                    r = await client.get(url, headers=headers)
                    r.raise_for_status()
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404 and page == 1:
                        await interaction.followup.send(f"Could not find commits for repository `{repo}`. It might not have any commits or the repository does not exist.")
                        return
                    elif e.response.status_code == 404: # No more pages
                        break
                    else:
                        await interaction.followup.send(f"An error occurred while fetching commits: {e}")
                        return
                except httpx.RequestError as e:
                    await interaction.followup.send(f"An error occurred while making the request: {e}")
                    return

                data = r.json()
                if not data:
                    break
                all_commits.extend(data)
                page += 1

        if not all_commits:
            await interaction.followup.send(f"No commits found for repository `{repo}`.")
            return

        view = CommitPaginator(all_commits, repo)
        await interaction.followup.send(embed=view._create_embed(), view=view)

async def setup(bot):
    await bot.add_cog(ChangelogCommand(bot))
