import discord
from discord import app_commands
from discord.ext import commands
import httpx
from datetime import datetime

COLOR_BLUE = 0x3498db

class Issue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    issue_group = app_commands.Group(name="issue", description="Commands for GitHub issues")

    async def _fetch_and_display_issue_list(self, interaction: discord.Interaction, owner: str, repo_name: str, state: str):
        headers = {"Accept": "application/vnd.github.v3+json"}
        url = f"https://api.github.com/repos/{owner}/{repo_name}/issues?state={state}"
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=headers)
            if r.status_code != 200:
                await interaction.followup.send(f"Could not fetch {state} issues for `{owner}/{repo_name}`. Status: {r.status_code}")
                return
            issues_data = r.json()

            if not issues_data:
                await interaction.followup.send(f"No {state} issues found for `{owner}/{repo_name}`.")
                return

            embed = discord.Embed(
                title=f"{state.capitalize()} Issues for {owner}/{repo_name}",
                color=COLOR_BLUE
            )
            for issue_item in issues_data:
                title = issue_item["title"]
                number = issue_item["number"]
                html_url = issue_item["html_url"]
                user = issue_item["user"]["login"]
                embed.add_field(name=f"#{number}: {title}", value=f"Opened by {user} ([Link]({html_url}))", inline=False)

            await interaction.followup.send(embed=embed)

    async def _fetch_and_display_single_issue(self, interaction: discord.Interaction, owner: str, repo_name: str, issue_id: int):
        headers = {"Accept": "application/vnd.github.v3+json"}
        url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{issue_id}"
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=headers)
            if r.status_code != 200:
                await interaction.followup.send(f"Could not find issue `#{issue_id}` in `{owner}/{repo_name}`. Status: {r.status_code}")
                return
            issue_data = r.json()

            title = issue_data["title"]
            number = issue_data["number"]
            user = issue_data["user"]["login"]
            state = issue_data["state"]
            html_url = issue_data["html_url"]
            created_at = datetime.strptime(issue_data["created_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S UTC")
            body = issue_data["body"] if issue_data["body"] else "No description provided."
            comments = issue_data["comments"]

            embed = discord.Embed(
                title=f"Issue #{number}: {title}",
                url=html_url,
                description=body,
                color=COLOR_BLUE
            )
            embed.add_field(name="Repository", value=f"{owner}/{repo_name}", inline=True)
            embed.add_field(name="Status", value=state.capitalize(), inline=True)
            embed.add_field(name="Opened By", value=user, inline=True)
            embed.add_field(name="Created At", value=created_at, inline=False)
            embed.add_field(name="Comments", value=str(comments), inline=True)

            await interaction.followup.send(embed=embed)

    @issue_group.command(name="open", description="Get information on open GitHub issues")
    @app_commands.describe(
        repo="Repository in the form of owner/repo (e.g. myferr/x3)",
        issue_id="Optional: Issue ID (e.g. 1). If not provided, lists all open issues."
    )
    async def issue_open(self, interaction: discord.Interaction, repo: str, issue_id: int = None):
        await interaction.response.defer()
        try:
            owner, repo_name = repo.split('/')
        except ValueError:
            await interaction.followup.send("Invalid repository format. Please use `owner/repo` (e.g., `myferr/x3`).")
            return

        if issue_id is None:
            await self._fetch_and_display_issue_list(interaction, owner, repo_name, "open")
        else:
            await self._fetch_and_display_single_issue(interaction, owner, repo_name, issue_id)

    @issue_group.command(name="closed", description="Get information on closed GitHub issues")
    @app_commands.describe(
        repo="Repository in the form of owner/repo (e.g. myferr/x3)",
        issue_id="Optional: Issue ID (e.g. 1). If not provided, lists all closed issues."
    )
    async def issue_closed(self, interaction: discord.Interaction, repo: str, issue_id: int = None):
        await interaction.response.defer()
        try:
            owner, repo_name = repo.split('/')
        except ValueError:
            await interaction.followup.send("Invalid repository format. Please use `owner/repo` (e.g., `myferr/x3`).")
            return

        if issue_id is None:
            await self._fetch_and_display_issue_list(interaction, owner, repo_name, "closed")
        else:
            await self._fetch_and_display_single_issue(interaction, owner, repo_name, issue_id)

async def setup(bot):
    await bot.add_cog(Issue(bot))