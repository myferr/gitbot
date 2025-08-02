import discord
from discord import app_commands
from discord.ext import commands
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
import os

COLOR_PURPLE = 0x9b59b6

class GitHubNotifications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.users = AsyncIOMotorClient(os.getenv("MONGO_URI")).gitbot.users
        from token_handler import TokenHandler
        self.token_handler = TokenHandler()

    @app_commands.command(name="notifications", description="Get your GitHub notifications via DM.")
    async def notifications(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user = await self.users.find_one({"discord_id": str(interaction.user.id)})
        if not user or "token" not in user:
            await interaction.followup.send("⚠️ You must authenticate first using `/auth`.", ephemeral=True)
            return

        token_handler = self.token_handler
        token = token_handler.decrypt(user["token"]) if user and user.get("token") else None
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        async with httpx.AsyncClient() as client:
            res = await client.get("https://api.github.com/notifications", headers=headers)

        if res.status_code != 200:
            await interaction.followup.send(f"❌ Failed to fetch notifications (status {res.status_code}).", ephemeral=True)
            return

        notifications = res.json()
        if not notifications:
            await interaction.followup.send("📭 You have no unread GitHub notifications.", ephemeral=True)
            return

        # Format a message with up to 10 notifications to avoid spamming
        lines = []
        for notif in notifications[:10]:
            repo_name = notif["repository"]["full_name"]
            subject = notif["subject"]["title"]
            notif_type = notif["subject"]["type"]
            url = notif["subject"].get("url") or ""
            # GitHub API URLs for notifications subject are API URLs; transform to HTML URLs:
            # For issues/PRs, replace api.github.com/repos/.../issues/123 with github.com/.../issues/123
            if url:
                url = url.replace("api.github.com/repos", "github.com").replace("/pulls/", "/pull/")
                url = url.replace("issues/", "issues/")
            lines.append(f"- **[{repo_name}]** {notif_type}: [{subject}]({url})")

        message = "Here are your latest GitHub notifications:\n\n" + "\n".join(lines)
        if len(notifications) > 10:
            message += f"\n\nAnd {len(notifications)-10} more..."

        try:
            await interaction.user.send(message)
            await interaction.followup.send("📬 I've sent your GitHub notifications to your DMs!", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ I couldn't DM you. Please check your privacy settings.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(GitHubNotifications(bot))

