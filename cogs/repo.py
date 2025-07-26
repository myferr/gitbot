import discord
from discord import app_commands
from discord.ext import commands
import httpx
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os

COLOR_PURPLE = 0x9b59b6

# Modal that gathers all info at once (including license & visibility as text inputs)
class RepoCreateModal(discord.ui.Modal, title="Create GitHub Repository"):
    name = discord.ui.TextInput(label="Repository Name", placeholder="my-new-repo", max_length=100)
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, required=False)
    license = discord.ui.TextInput(
        label="License Key",
        placeholder="mit, apache-2.0, gpl-3.0, etc. (leave blank for no license)",
        required=False,
        max_length=50
    )
    visibility = discord.ui.TextInput(
        label="Visibility",
        placeholder="public or private",
        max_length=7
    )

    def __init__(self, token: str, valid_licenses: set):
        super().__init__()
        self.token = token
        self.valid_licenses = valid_licenses

    async def on_submit(self, interaction: discord.Interaction):
        license_key = self.license.value.strip().lower()
        visibility = self.visibility.value.strip().lower()

        if license_key and license_key not in self.valid_licenses:
            await interaction.response.send_message(
                f"❌ Invalid license key `{license_key}`. Please use a valid SPDX license identifier or leave blank.",
                ephemeral=True
            )
            return

        if visibility not in {"public", "private"}:
            await interaction.response.send_message(
                f"❌ Invalid visibility `{visibility}`. Please enter `public` or `private`.",
                ephemeral=True
            )
            return

        payload = {
            "name": self.name.value,
            "description": self.description.value or "",
            "private": (visibility == "private"),
            "auto_init": True,
        }
        if license_key:
            payload["license_template"] = license_key

        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }

        async with httpx.AsyncClient() as client:
            res = await client.post("https://api.github.com/user/repos", headers=headers, json=payload)

        if res.status_code == 201:
            repo = res.json()
            await interaction.response.send_message(
                f"✅ Repository created: [{repo['full_name']}]({repo['html_url']})",
                ephemeral=True
            )
        else:
            msg = res.json().get("message", "")
            await interaction.response.send_message(
                f"❌ Failed to create repository (status {res.status_code}): {msg}",
                ephemeral=True
            )




class RepoCommands(commands.GroupCog, name="repo"):
    def __init__(self, bot):
        self.bot = bot
        self.users = AsyncIOMotorClient(os.getenv("MONGO_URI")).gitbot.users

    @app_commands.command(name="view", description="View GitHub repository information.")
    @app_commands.describe(repo="Format `owner/repo`.")
    async def view(self, interaction: discord.Interaction, repo: str):
        await interaction.response.defer()
        try:
            owner, name = repo.split('/')
        except ValueError:
            await interaction.followup.send("Invalid repository format. Use `owner/repo`.", ephemeral=True)
            return

        url = f"https://api.github.com/repos/{owner}/{name}"
        headers = {"Accept": "application/vnd.github.v3+json"}

        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers)

            if res.status_code == 404:
                user = await self.users.find_one({"discord_id": str(interaction.user.id)})
                if not user or "token" not in user:
                    await interaction.followup.send("Repo not found or private. Use `/auth` to authenticate.", ephemeral=True)
                    return

                token = user["token"]
                headers["Authorization"] = f"token {token}"
                res = await client.get(url, headers=headers)

                if res.status_code == 200:
                    data = res.json()
                    if data.get("private") and data.get("owner", {}).get("login", "").lower() != user.get("github_user", "").lower():
                        await interaction.followup.send("This is a private repo and you are not the owner.", ephemeral=True)
                        return
                else:
                    await interaction.followup.send(f"Repo not found. Status: {res.status_code}", ephemeral=True)
                    return
            elif res.status_code != 200:
                await interaction.followup.send(f"GitHub API error: {res.status_code}", ephemeral=True)
                return
            else:
                data = res.json()

        updated = datetime.strptime(data["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
        embed = discord.Embed(
            title=data["full_name"],
            url=data["html_url"],
            description=data.get("description", "No description."),
            color=COLOR_PURPLE
        )
        embed.add_field(name="Language", value=data.get("language", "Unknown"))
        embed.add_field(name="⭐ Stars", value=str(data.get("stargazers_count", 0)))
        embed.add_field(name="🍴 Forks", value=str(data.get("forks_count", 0)))
        embed.add_field(name="Updated", value=updated.strftime("%Y-%m-%d %H:%M UTC"))
        if data.get("private"):
            embed.set_footer(text="🔒 Private repository")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="create", description="Create a new GitHub repository (modal).")
    async def create(self, interaction: discord.Interaction):
        user = await self.users.find_one({"discord_id": str(interaction.user.id)})
        if not user or "token" not in user:
            await interaction.response.send_message("⚠️ You must authenticate first using `/auth`.", ephemeral=True)
            return

        from token_handler import TokenHandler
        token_handler = TokenHandler()
        token = token_handler.decrypt(user["token"]) if user and user.get("token") else None

        # Fetch license keys to validate input
        async with httpx.AsyncClient() as client:
            lic_res = await client.get("https://api.github.com/licenses?per_page=100", headers={"Accept": "application/vnd.github.v3+json"})

        valid_licenses = set()
        if lic_res.status_code == 200:
            valid_licenses = {lic["key"] for lic in lic_res.json()}

        modal = RepoCreateModal(token, valid_licenses)
        await interaction.response.send_modal(modal)


async def setup(bot):
    await bot.add_cog(RepoCommands(bot))
