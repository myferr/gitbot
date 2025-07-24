import discord
from discord import app_commands
from discord.ext import commands
import httpx
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os

COLOR_PURPLE = 0x9b59b6

class RepoCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
        self.users_collection = self.mongo_client.gitbot.users

    @app_commands.command(name="repo", description="Provides detailed information about a specified GitHub repository.")
    @app_commands.describe(repo="The repository in the format `owner/repo` (e.g., `myferr/x3`).")
    async def repo(self, interaction: discord.Interaction, repo: str):
        await interaction.response.defer()
        try:
            owner_login, repo_name = repo.split('/')
        except ValueError:
            await interaction.followup.send("Invalid repository format. Use `owner/repo` (e.g., `myferr/x3`).")
            return

        headers = {"Accept": "application/vnd.github.v3+json"}
        url = f"https://api.github.com/repos/{owner_login}/{repo_name}"
        
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers)
            
            if res.status_code == 200:
                data = res.json()
            elif res.status_code == 404:
                discord_id = str(interaction.user.id)
                user = await self.users_collection.find_one({"discord_id": discord_id})
                
                if not user or "token" not in user:
                    await interaction.followup.send(f"Repository `{repo}` not found or it is a private repository for which you are not authenticated. Use `/auth` to authenticate.")
                    return
                
                token = user["token"]
                auth_headers = {
                    "Accept": "application/vnd.github.v3+json",
                    "Authorization": f"token {token}"
                }
                auth_res = await client.get(url, headers=auth_headers)
                
                if auth_res.status_code == 200:
                    data = auth_res.json()
                    if data.get("private"):
                        if data.get("owner", {}).get("login", "").lower() != user.get("github_user", "").lower():
                            await interaction.followup.send("This repository is private and you are not the owner.")
                            return
                elif auth_res.status_code == 404:
                    await interaction.followup.send(f"Repository `{repo}` not found.")
                    return
                else:
                    await interaction.followup.send(f"Failed to fetch repository info. Status: {auth_res.status_code}")
                    return
            else:
                await interaction.followup.send(f"Failed to fetch repository info. Status: {res.status_code}")
                return

        # Prepare embed
        name = data["name"]
        owner = data["owner"]["login"]
        description = data.get("description", "No description.")
        lang = data.get("language", "Unknown")
        stars = data.get("stargazers_count", 0)
        forks = data.get("forks_count", 0)
        updated = datetime.strptime(data["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
        updated_str = updated.strftime("%Y-%m-%d %H:%M:%S UTC")
        html_url = data["html_url"]
        is_private = data.get("private", False)

        embed = discord.Embed(
            title=f"{owner}/{name}",
            url=html_url,
            description=description,
            color=COLOR_PURPLE
        )
        embed.add_field(name="Owner", value=owner, inline=True)
        embed.add_field(name="Language", value=lang, inline=True)
        embed.add_field(name="Stars", value=str(stars), inline=True)
        embed.add_field(name="Forks", value=str(forks), inline=True)
        embed.add_field(name="Last Updated", value=updated_str, inline=False)
        if is_private:
            embed.set_footer(text="Private repository")

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RepoCommands(bot))

