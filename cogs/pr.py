import discord
from discord import app_commands
from discord.ext import commands
import httpx
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os

COLOR_BLUE = 0x3498db

class PullRequest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
        self.users_collection = self.mongo_client.gitbot.users

    pr_group = app_commands.Group(name="pr", description="Commands for GitHub pull requests")

    async def _fetch_and_display_pr_list(self, interaction: discord.Interaction, owner: str, repo_name: str, state: str):
        headers = {"Accept": "application/vnd.github.v3+json"}
        url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls?state={state}"
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=headers)
            if r.status_code != 200:
                await interaction.followup.send(f"Could not fetch {state} pull requests for `{owner}/{repo_name}`. Status: {r.status_code}")
                return
            prs_data = r.json()

            if not prs_data:
                await interaction.followup.send(f"No {state} pull requests found for `{owner}/{repo_name}`.")
                return

            embed = discord.Embed(
                title=f"{state.capitalize()} Pull Requests for {owner}/{repo_name}",
                color=COLOR_BLUE
            )
            for pr_item in prs_data:
                title = pr_item["title"]
                number = pr_item["number"]
                html_url = pr_item["html_url"]
                user = pr_item["user"]["login"]
                embed.add_field(name=f"#{number}: {title}", value=f"Opened by {user} ([Link]({html_url}))", inline=False)

            await interaction.followup.send(embed=embed)

    async def _fetch_and_display_single_pr(self, interaction: discord.Interaction, owner: str, repo_name: str, pr_id: int):
        headers = {"Accept": "application/vnd.github.v3+json"}
        url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_id}"
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=headers)
            if r.status_code != 200:
                await interaction.followup.send(f"Could not find pull request `#{pr_id}` in `{owner}/{repo_name}`. Status: {r.status_code}")
                return
            pr_data = r.json()

            title = pr_data["title"]
            number = pr_data["number"]
            user = pr_data["user"]["login"]
            state = pr_data["state"]
            html_url = pr_data["html_url"]
            created_at = datetime.strptime(pr_data["created_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S UTC")
            body = pr_data["body"] if pr_data["body"] else "No description provided."
            commits = pr_data["commits"]
            additions = pr_data["additions"]
            deletions = pr_data["deletions"]
            changed_files = pr_data["changed_files"]

            embed = discord.Embed(
                title=f"Pull Request #{number}: {title}",
                url=html_url,
                description=body,
                color=COLOR_BLUE
            )
            embed.add_field(name="Repository", value=f"{owner}/{repo_name}", inline=True)
            embed.add_field(name="Status", value=state.capitalize(), inline=True)
            embed.add_field(name="Opened By", value=user, inline=True)
            embed.add_field(name="Created At", value=created_at, inline=False)
            embed.add_field(name="Commits", value=str(commits), inline=True)
            embed.add_field(name="Additions", value=str(additions), inline=True)
            embed.add_field(name="Deletions", value=str(deletions), inline=True)
            embed.add_field(name="Files Changed", value=str(changed_files), inline=True)

            await interaction.followup.send(embed=embed)

    @pr_group.command(name="open", description="Get information on open GitHub pull requests")
    @app_commands.describe(
        repo="Repository in the form of owner/repo (e.g. myferr/x3)",
        pr_id="Optional: Pull request ID (e.g. 1). If not provided, lists all open PRs."
    )
    async def pr_open(self, interaction: discord.Interaction, repo: str, pr_id: int = None):
        await interaction.response.defer()
        try:
            owner, repo_name = repo.split('/')
        except ValueError:
            await interaction.followup.send("Invalid repository format. Please use `owner/repo` (e.g., `myferr/x3`).")
            return

        if pr_id is None:
            await self._fetch_and_display_pr_list(interaction, owner, repo_name, "open")
        else:
            await self._fetch_and_display_single_pr(interaction, owner, repo_name, pr_id)

    @pr_group.command(name="closed", description="Get information on closed GitHub pull requests")
    @app_commands.describe(
        repo="Repository in the form of owner/repo (e.g. myferr/x3)",
        pr_id="Optional: Pull request ID (e.g. 1). If not provided, lists all closed PRs."
    )
    async def pr_closed(self, interaction: discord.Interaction, repo: str, pr_id: int = None):
        await interaction.response.defer()
        try:
            owner, repo_name = repo.split('/')
        except ValueError:
            await interaction.followup.send("Invalid repository format. Please use `owner/repo` (e.g., `myferr/x3`).")
            return

        if pr_id is None:
            await self._fetch_and_display_pr_list(interaction, owner, repo_name, "closed")
        else:
            await self._fetch_and_display_single_pr(interaction, owner, repo_name, pr_id)

    @pr_group.command(name="merge", description="Merge a pull request (requires authentication)")
    @app_commands.describe(
        repo="Repository in the form of owner/repo (e.g. myferr/x3)",
        pr_id="Pull request ID (e.g. 1)"
    )
    async def pr_merge(self, interaction: discord.Interaction, repo: str, pr_id: int):
        await interaction.response.defer(ephemeral=True)
        discord_id = str(interaction.user.id)
        user = await self.users_collection.find_one({"discord_id": discord_id})
        if not user:
            await interaction.followup.send("❌ You must link your GitHub account using `/auth` before merging PRs.", ephemeral=True)
            return

        token = user.get("token")
        if not token:
            await interaction.followup.send("❌ Your GitHub token is missing. Please re-authenticate with `/auth`.", ephemeral=True)
            return

        try:
            owner, repo_name = repo.split('/')
        except ValueError:
            await interaction.followup.send("Invalid repository format. Use `owner/repo`.", ephemeral=True)
            return

        url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_id}/merge"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        async with httpx.AsyncClient() as client:
            res = await client.put(url, headers=headers)
            data = res.json()

        if res.status_code == 200 and data.get("merged"):
            await interaction.followup.send(f"✅ PR #{pr_id} has been merged successfully.", ephemeral=True)
        elif res.status_code == 405:
            await interaction.followup.send(f"❌ PR #{pr_id} cannot be merged (maybe conflicts).", ephemeral=True)
        else:
            message = data.get("message", "Unknown error.")
            await interaction.followup.send(f"❌ Failed to merge PR #{pr_id}: {message}", ephemeral=True)

    @pr_group.command(name="close", description="Close a pull request without merging (requires authentication)")
    @app_commands.describe(
        repo="Repository in the form of owner/repo (e.g. myferr/x3)",
        pr_id="Pull request ID (e.g. 1)"
    )
    async def pr_close(self, interaction: discord.Interaction, repo: str, pr_id: int):
        await interaction.response.defer(ephemeral=True)
        discord_id = str(interaction.user.id)
        user = await self.users_collection.find_one({"discord_id": discord_id})
        if not user:
            await interaction.followup.send("❌ You must link your GitHub account using `/auth` before closing PRs.", ephemeral=True)
            return

        token = user.get("token")
        if not token:
            await interaction.followup.send("❌ Your GitHub token is missing. Please re-authenticate with `/auth`.", ephemeral=True)
            return

        try:
            owner, repo_name = repo.split('/')
        except ValueError:
            await interaction.followup.send("Invalid repository format. Use `owner/repo`.", ephemeral=True)
            return

        url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_id}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        json_data = {
            "state": "closed"
        }
        async with httpx.AsyncClient() as client:
            res = await client.patch(url, headers=headers, json=json_data)
            data = res.json()

        if res.status_code == 200 and data.get("state") == "closed":
            await interaction.followup.send(f"✅ PR #{pr_id} has been closed.", ephemeral=True)
        else:
            message = data.get("message", "Unknown error.")
            await interaction.followup.send(f"❌ Failed to close PR #{pr_id}: {message}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(PullRequest(bot))

