# gitbot/cogs/file.py

import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import base64
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
mongo = MongoClient(os.getenv("MONGO_URI"))
GITHUB_API = "https://api.github.com"

class FileModal(discord.ui.Modal):
    def __init__(self, title, repo, path, token, is_edit, default_content=""):
        super().__init__(title=title)
        self.repo = repo
        self.path = path
        self.token = token
        self.is_edit = is_edit

        self.branch = discord.ui.TextInput(label="Branch", placeholder="main", default="main", required=True)
        self.commit_msg = discord.ui.TextInput(label="Commit message", placeholder="Edited via GitBot", required=False)
        self.content = discord.ui.TextInput(label="File Content", style=discord.TextStyle.paragraph, default=default_content, required=True, max_length=3900)

        self.add_item(self.branch)
        self.add_item(self.commit_msg)
        self.add_item(self.content)

    async def on_submit(self, interaction: discord.Interaction):
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json"
        }

        url = f"{GITHUB_API}/repos/{self.repo}/contents/{self.path}"
        commit_msg = self.commit_msg.value or ("Edited via GitBot" if self.is_edit else "Created via GitBot")
        branch = self.branch.value

        sha = None
        if self.is_edit:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}?ref={branch}", headers=headers) as r:
                    if r.status == 200:
                        data = await r.json()
                        sha = data.get("sha")
                    else:
                        embed = discord.Embed(title="Error", description="❌ Could not fetch file SHA.", color=discord.Color.red())
                        return await interaction.response.send_message(embed=embed)

        payload = {
            "message": commit_msg,
            "content": base64.b64encode(self.content.value.encode()).decode(),
            "branch": branch
        }
        if sha:
            payload["sha"] = sha

        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=payload) as r:
                if r.status in (200, 201):
                    verb = "updated" if self.is_edit else "created"
                    embed = discord.Embed(title="Success", description=f"✅ Successfully {verb} `{self.path}` on `{branch}`.", color=discord.Color.green())
                    await interaction.response.send_message(embed=embed)
                else:
                    text = await r.text()
                    embed = discord.Embed(title="GitHub Error", description=f"""❌ GitHub error:
```
{text}
```""", color=discord.Color.red())
                    await interaction.response.send_message(embed=embed)


class File(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    file_group = app_commands.Group(name="file", description="Manage GitHub repository files")

    async def get_user_token(self, discord_id: int):
        user = mongo.gitbot.users.find_one({"discord_id": str(discord_id)})
        return user.get("token") if user else None

    @file_group.command(name="create", description="Create a new file in a repository")
    @app_commands.describe(repo="owner/repo", path="Path to the file")
    async def create(self, interaction: discord.Interaction, repo: str, path: str):
        token = await self.get_user_token(interaction.user.id)
        if not token:
            embed = discord.Embed(title="Error", description="❌ Link your GitHub account first.", color=discord.Color.red())
            return await interaction.response.send_message(embed=embed)
        await interaction.response.send_modal(FileModal("Create File", repo, path, token, is_edit=False))

    @file_group.command(name="edit", description="Edit an existing file in a repository")
    @app_commands.describe(repo="owner/repo", path="Path to the file")
    async def edit(self, interaction: discord.Interaction, repo: str, path: str):
        token = await self.get_user_token(interaction.user.id)
        if not token:
            embed = discord.Embed(title="Error", description="❌ Link your GitHub account first.", color=discord.Color.red())
            return await interaction.response.send_message(embed=embed)

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"
        }
        url = f"{GITHUB_API}/repos/{repo}/contents/{path}?ref=main"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as r:
                if r.status != 200:
                    embed = discord.Embed(title="Error", description="❌ Could not fetch file.", color=discord.Color.red())
                    return await interaction.response.send_message(embed=embed)
                data = await r.json()
                content = base64.b64decode(data["content"]).decode()

        await interaction.response.send_modal(FileModal("Edit File", repo, path, token, is_edit=True, default_content=content))

    @file_group.command(name="remove", description="Delete a file from a repository")
    @app_commands.describe(repo="owner/repo", path="Path to the file", branch="Branch", commit_msg="Commit message")
    async def remove(self, interaction: discord.Interaction, repo: str, path: str, branch: str = "main", commit_msg: str = "Deleted via GitBot"):
        token = await self.get_user_token(interaction.user.id)
        if not token:
            embed = discord.Embed(title="Error", description="❌ Link your GitHub account first.", color=discord.Color.red())
            return await interaction.response.send_message(embed=embed)

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"
        }
        url = f"{GITHUB_API}/repos/{repo}/contents/{path}?ref={branch}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as r:
                if r.status != 200:
                    embed = discord.Embed(title="Error", description="❌ File not found.", color=discord.Color.red())
                    return await interaction.response.send_message(embed=embed)
                data = await r.json()
                sha = data.get("sha")

            async with session.delete(f"{GITHUB_API}/repos/{repo}/contents/{path}", headers=headers, json={
                "message": commit_msg,
                "sha": sha,
                "branch": branch
            }) as r:
                if r.status == 200:
                    embed = discord.Embed(title="Success", description="✅ File deleted.", color=discord.Color.green())
                    await interaction.response.send_message(embed=embed)
                else:
                    embed = discord.Embed(title="Error", description="❌ Failed to delete file.", color=discord.Color.red())
                    await interaction.response.send_message(embed=embed)

    @file_group.command(name="view", description="View the contents of a file")
    @app_commands.describe(repo="owner/repo", path="Path to the file", branch="Branch name")
    async def view(self, interaction: discord.Interaction, repo: str, path: str, branch: str = "main"):
        token = await self.get_user_token(interaction.user.id)
        if not token:
            embed = discord.Embed(title="Error", description="❌ Link your GitHub account first.", color=discord.Color.red())
            return await interaction.response.send_message(embed=embed)

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"
        }
        url = f"{GITHUB_API}/repos/{repo}/contents/{path}?ref={branch}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as r:
                if r.status != 200:
                    embed = discord.Embed(title="Error", description="❌ Could not fetch file.", color=discord.Color.red())
                    return await interaction.response.send_message(embed=embed)
                data = await r.json()
                content = base64.b64decode(data["content"]).decode()

        if len(content) > 1900:
            content = content[:1900] + "\n... (truncated)"

        file_extension = path.split('.')[-1] if '.' in path else ''
        embed = discord.Embed(title=f"Content of `{path}`", description=f"```{file_extension}\n{content}\n```", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    @file_group.command(name="tree", description="Lists an ASCII styled file tree of the given repository")
    @app_commands.describe(repo="owner/repo (e.g. myferr/gitbot)", branch="Branch name (default: main)")
    async def tree(self, interaction: discord.Interaction, repo: str, branch: str = "main"):
        token = await self.get_user_token(interaction.user.id)
        if not token:
            embed = discord.Embed(title="Error", description="❌ Link your GitHub account first.", color=discord.Color.red())
            return await interaction.response.send_message(embed=embed)

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get the SHA of the default branch's tree
        repo_url = f"{GITHUB_API}/repos/{repo}"
        async with aiohttp.ClientSession() as session:
            async with session.get(repo_url, headers=headers) as r:
                if r.status != 200:
                    embed = discord.Embed(title="Error", description=f"❌ Could not fetch repository info for `{repo}`. Status: {r.status}", color=discord.Color.red())
                    return await interaction.response.send_message(embed=embed)
                repo_data = await r.json()
                default_branch = repo_data.get("default_branch", "main") # Use default_branch from repo info

        tree_url = f"{GITHUB_API}/repos/{repo}/git/trees/{default_branch}?recursive=1"

        async with aiohttp.ClientSession() as session:
            async with session.get(tree_url, headers=headers) as r:
                if r.status != 200:
                    embed = discord.Embed(title="Error", description=f"❌ Could not fetch tree for `{repo}` on branch `{default_branch}`. Status: {r.status}", color=discord.Color.red())
                    return await interaction.response.send_message(embed=embed)
                tree_data = await r.json()

        tree_output = self.generate_tree_string(tree_data.get("tree", []))

        if len(tree_output) > 1900:
            tree_output = tree_output[:1900] + "\n... (truncated)"

        embed = discord.Embed(title=f"File Tree for `{repo}`", description=f"```\n{tree_output}\n```", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    def generate_tree_string(self, tree_data):
        tree = {}
        for item in tree_data:
            path_parts = item["path"].split("/")
            current_level = tree
            for part in path_parts:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
            current_level["_type"] = item["type"]

        def build_ascii_tree_recursive(node, indent_prefix="", is_last_parent=False):
            output = ""
            sorted_keys = sorted([k for k in node.keys() if k != "_type"])

            for i, key in enumerate(sorted_keys):
                is_last_child = (i == len(sorted_keys) - 1)
                item_type = node[key].get("_type")

                line_prefix = "└── " if is_last_child else "├── "
                output += f"{indent_prefix}{line_prefix}{key}"

                if item_type == "blob":
                    output += "\n"
                else: # It's a directory
                    output += "/\n"
                    new_indent_prefix = indent_prefix + ("    " if is_last_parent else "│   ")
                    output += build_ascii_tree_recursive(node[key], new_indent_prefix, is_last_child)
            return output

        final_output = ""
        root_keys = sorted([k for k in tree.keys() if k != "_type"])
        for i, key in enumerate(root_keys):
            is_last_root_item = (i == len(root_keys) - 1)
            item_type = tree[key].get("_type")

            if item_type == "blob":
                final_output += f"{key}\n"
            else: # It's a directory
                final_output += f"{key}/\n"
                initial_child_indent = "    " if is_last_root_item else "│   "
                final_output += build_ascii_tree_recursive(tree[key], initial_child_indent, is_last_root_item)

        return final_output

    async def cog_load(self):
        pass

async def setup(bot):
    await bot.add_cog(File(bot))

