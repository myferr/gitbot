import os
import discord
import aiohttp
from discord.ext import commands
from discord import app_commands, Interaction, ui
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

GITHUB_API = "https://api.github.com"

def make_embed(title: str, description: str, color=discord.Color.blurple()) -> discord.Embed:
    return discord.Embed(title=title, description=description, color=color)

class TagPaginator(ui.View):
    def __init__(self, tags: list[dict], per_page: int = 5):
        super().__init__(timeout=60)
        self.tags = tags
        self.per_page = per_page
        self.page = 0
        self.max_page = (len(tags) - 1) // per_page

        self.prev_button.disabled = True
        self.next_button.disabled = self.max_page == 0

    def get_embed(self) -> discord.Embed:
        start = self.page * self.per_page
        end = start + self.per_page
        current_tags = self.tags[start:end]

        embed = make_embed(f"Tags Page {self.page + 1}/{self.max_page + 1}", "")
        for tag in current_tags:
            tag_name = tag['ref'].split('/')[-1]
            tag_url = tag['url']
            embed.add_field(name=tag_name, value=f"[View Tag]({tag_url})", inline=False)
        return embed

    @ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: Interaction, _):
        self.page -= 1
        self.prev_button.disabled = self.page == 0
        self.next_button.disabled = False
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: Interaction, _):
        self.page += 1
        self.next_button.disabled = self.page == self.max_page
        self.prev_button.disabled = False
        await interaction.response.edit_message(embed=self.get_embed(), view=self)


class Tag(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        mongo = AsyncIOMotorClient(os.getenv("MONGO_URI"))
        self.users = mongo.gitbot.users

    async def get_token(self, discord_id: str) -> Optional[str]:
        user = await self.users.find_one({"discord_id": discord_id})
        return user.get("token") if user else None

    async def github_get(self, url: str, token: Optional[str] = None):
        headers = {"Authorization": f"token {token}"} if token else {}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                return await resp.json()

    async def github_post(self, url: str, token: str, data: dict):
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                return await resp.json(), resp.status

    async def github_delete(self, url: str, token: str):
        headers = {"Authorization": f"token {token}"}
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=headers) as resp:
                return resp.status

    tag_group = app_commands.Group(name="tag", description="GitHub Tag commands")

    @tag_group.command(name="info", description="Get tag information (no login required)")
    async def tag_info(
        self,
        interaction: Interaction,
        repository: str,
        tag: str
    ):
        await interaction.response.defer()
        url = f"{GITHUB_API}/repos/{repository}/git/ref/tags/{tag}"
        data = await self.github_get(url)

        if "object" not in data:
            return await interaction.followup.send(":x: Tag not found.")

        tag_sha = data["object"]["sha"]
        tag_url = data["object"]["url"]

        embed = make_embed(f"Tag: {tag}", f"[View Tag Object]({tag_url})")
        embed.add_field(name="SHA", value=tag_sha)
        embed.set_footer(text=repository)
        await interaction.followup.send(embed=embed)

    @tag_group.command(name="list", description="List all tags for a repository")
    async def tag_list(
        self,
        interaction: Interaction,
        repository: str
    ):
        await interaction.response.defer()
        url = f"{GITHUB_API}/repos/{repository}/git/refs/tags"
        tags = await self.github_get(url)

        if not isinstance(tags, list):
            return await interaction.followup.send(":x: Could not fetch tags.")

        if not tags:
            return await interaction.followup.send("No tags found.")

        view = TagPaginator(tags)
        await interaction.followup.send(embed=view.get_embed(), view=view)

    @tag_group.command(name="create", description="Create and push a new tag")
    async def tag_create(
        self,
        interaction: Interaction,
        repository: str,
        tag: str,
        message: str
    ):
        token = await self.get_token(str(interaction.user.id))
        if not token:
            return await interaction.response.send_message("❌ You need to `/auth` first.", ephemeral=True)

        await interaction.response.defer()
        repo_url = f"{GITHUB_API}/repos/{repository}"
        repo_data = await self.github_get(repo_url, token=token)
        default_branch = repo_data.get("default_branch", "main")

        branch_url = f"{repo_url}/git/ref/heads/{default_branch}"
        ref_data = await self.github_get(branch_url, token=token)
        commit_sha = ref_data.get("object", {}).get("sha")

        if not commit_sha:
            return await interaction.followup.send(":x: Could not get base commit SHA.")

        tag_obj = {
            "tag": tag,
            "message": message,
            "object": commit_sha,
            "type": "commit",
            "tagger": {
                "name": interaction.user.name,
                "email": f"{interaction.user.id}@users.noreply.github.com",
                "date": interaction.created_at.isoformat()
            }
        }

        tag_response, status = await self.github_post(f"{repo_url}/git/tags", token, tag_obj)
        if status >= 400:
            return await interaction.followup.send(f":x: GitHub Error: {tag_response}")

        ref_data = {
            "ref": f"refs/tags/{tag}",
            "sha": tag_response["sha"]
        }

        ref_response, status = await self.github_post(f"{repo_url}/git/refs", token, ref_data)
        if status >= 400:
            return await interaction.followup.send(f":x: GitHub Error: {ref_response}")

        embed = make_embed("✅ Tag Created", f"[View Tag]({ref_response['url']})")
        embed.add_field(name="Repository", value=repository)
        embed.add_field(name="Tag", value=tag)
        await interaction.followup.send(embed=embed)

    @tag_group.command(name="remove", description="Delete a tag from a repository")
    async def tag_remove(
        self,
        interaction: Interaction,
        repository: str,
        tag: str
    ):
        token = await self.get_token(str(interaction.user.id))
        if not token:
            return await interaction.response.send_message("❌ You need to `/auth` first.", ephemeral=True)

        await interaction.response.defer()
        url = f"{GITHUB_API}/repos/{repository}/git/refs/tags/{tag}"
        status = await self.github_delete(url, token)

        if status == 204:
            await interaction.followup.send(f"✅ Tag `{tag}` deleted from `{repository}`.")
        else:
            await interaction.followup.send(":x: Failed to delete tag. Make sure it exists.")

    async def setup(self):
        self.bot.tree.add_command(self.tag_group)


async def setup(bot):
    await bot.add_cog(Tag(bot))

