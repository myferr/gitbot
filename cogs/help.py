import discord
from discord.ext import commands
from discord import app_commands
from pymongo import MongoClient
import os

# Mongo setup (adjust if you're already using a global db client elsewhere)
MONGO_URI = os.getenv("MONGO_URI")
mongo = MongoClient(MONGO_URI)
users_col = mongo.gitbot.users

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="List all GitBot commands")
    async def help(self, interaction: discord.Interaction):
        user = users_col.find_one({"discord_id": str(interaction.user.id)})
        is_authed = bool(user and user.get("token"))

        auth_status = "✅ You are authenticated!" if is_authed else "❌ You are not authenticated.\nUse `/auth` to link your GitHub account."

        embed = discord.Embed(
            title="📘 GitBot Command Reference",
            description=auth_status,
            color=discord.Color.green() if is_authed else discord.Color.red()
        )

        embed.add_field(
            name="🔐 Authentication",
            value=(
                "`/auth` – Link your GitHub account.\n"
                "`/unauth` – Unlink your GitHub account.\n"
                "`/me` – Show your GitHub link status and profile."
            ),
            inline=False
        )

        embed.add_field(
            name="📁 Repositories",
            value=(
                "`/repo` – View repository info.\n"
                "`/repo create` – Create a new repo (modal)."
            ),
            inline=False
        )

        embed.add_field(
            name="🗃️ Files",
            value=(
                "`/file view` – View a file in a repo.\n"
                "`/file create` – Create a new file with content.\n"
                "`/file edit` – Edit a file (via modal).\n"
                "`/file remove` – Delete a file from the repo.\n"
                "`/file tree` - See the file tree of a repository"
            ),
            inline=False
        )

        embed.add_field(
            name="💬 Comments",
            value=(
                "`/pr comments` – List comments on a PR.\n"
                "`/pr comment` – Add a comment to a PR.\n"
                "`/issue comments` – List comments on an issue.\n"
                "`/issue comment` – Add a comment to an issue."
            ),
            inline=False
        )

        embed.add_field(
            name="🔀 Pull Requests",
            value=(
                "`/pr open` – List open pull requests.\n"
                "`/pr closed` – List closed pull requests.\n"
                "`/pr merge` – Merge a PR.\n"
                "`/pr close` – Close a PR."
            ),
            inline=False
        )

        embed.add_field(
            name="🐞 Issues",
            value=(
                "`/issue open` – List open issues.\n"
                "`/issue create` – Create a new issue.\n"
                "`/issue close` – Close an issue."
            ),
            inline=False
        )

        embed.add_field(
            name="🏷️ Tags",
            value=(
                "`/tag list` – List tags.\n"
                "`/tag create` – Create a new tag.\n"
                "`/tag info` - Get information on a tag"
                "`/tag remove` – Delete a tag."
            ),
            inline=False
        )

        embed.add_field(
            name="📬 Notifications",
            value="`/notifications` – DM your GitHub unread notifications.",
            inline=False
        )


        embed.set_footer(text="GitBot by myferr | https://github.com/myferr")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))

