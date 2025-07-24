import discord
from discord import app_commands
from discord.ext import commands

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Shows this help message.")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="GitBot Help",
            description="GitBot is a Discord bot that allows you to interact with GitHub.",
            color=0x7289da
        )
        embed.add_field(
            name="Authentication",
            value="`/auth`: Link your GitHub account with GitBot.\n"
                  "`/unauth`: Unlink your GitHub account from GitBot.\n"
                  "`/me`: Show your GitHub authentication status and profile info.",
            inline=False
        )
        embed.add_field(
            name="Repositories",
            value="`/repo view <owner/repo>`: View GitHub repository information.\n"
                  "`/repo create`: Create a new GitHub repository.\n"
                  "`/releases <owner/repo>`: Lists the latest releases of a GitHub repository.\n"
                  "`/release <owner/repo> <tag>`: Shows information about a specific release.\n"
                  "`/changelog <owner/repo>`: Lists recent commits (changelog) for a GitHub repository.\n"
                  "`/commit <owner/repo> <sha>`: Shows information about a specific commit.\n"
                  "`/license <owner/repo>`: Shows the license information for a GitHub repository.",
            inline=False
        )
        embed.add_field(
            name="Issues",
            value="`/issue open <owner/repo> [issue_id]`: Get information on open GitHub issues.\n"
                  "`/issue closed <owner/repo> [issue_id]`: Get information on closed GitHub issues.\n"
                  "`/issue new <owner/repo>`: Create a new GitHub issue.\n"
                  "`/issue close <owner/repo> <issue_id>`: Close a GitHub issue.",
            inline=False
        )
        embed.add_field(
            name="Pull Requests",
            value="`/pr open <owner/repo> [pr_id]`: Get information on open GitHub pull requests.\n"
                  "`/pr closed <owner/repo> [pr_id]`: Get information on closed GitHub pull requests.\n"
                  "`/pr merge <owner/repo> <pr_id>`: Merge a pull request.\n"
                  "`/pr close <owner/repo> <pr_id>`: Close a pull request without merging.",
            inline=False
        )
        embed.add_field(
            name="Gists",
            value="`/gist info <gist_id>`: Provides detailed information about a GitHub Gist.\n"
                  "`/gist content <gist_id> <filename>`: Shows the content of a specific file within a GitHub Gist.",
            inline=False
        )
        embed.add_field(
            name="Users",
            value="`/profile <username>`: Displays comprehensive information about a GitHub user.\n"
                  "`/top langs <username>`: Show top used languages for a user.\n"

                  "`/top repos <username>`: Show a user's repositories sorted by stars.",
            inline=False
        )
        embed.add_field(
            name="Files",
            value="`/file <owner/repo> <path>`: Shows the content of a file from a GitHub repository.",
            inline=False
        )
        embed.add_field(
            name="Notifications",
            value="`/notifications`: Get your GitHub notifications via DM.",
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))