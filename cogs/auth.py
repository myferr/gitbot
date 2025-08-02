import discord
from discord import app_commands
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient

class Auth(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client_id = os.getenv("GITHUB_CLIENT_ID")
        self.backend_base_url = os.getenv("BACKEND_BASE_URL", "http://localhost:2000")
        self.mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
        self.users_collection = self.mongo_client.gitbot.users
        from token_handler import TokenHandler
        self.token_handler = TokenHandler()

    @app_commands.command(name="auth", description="Link your GitHub account with GitBot")
    async def auth(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            discord_id = str(interaction.user.id)
            user = await self.users_collection.find_one({"discord_id": discord_id})
            if user:
                await interaction.followup.send(
                    "✅ You are already linked to GitHub user: "
                    f"`{user.get('github_user', 'unknown')}`",
                    ephemeral=True,
                )
                return

            oauth_url = f"{self.backend_base_url}/auth?discord={discord_id}&client_id={self.client_id}"
            embed = discord.Embed(
                title="🔗 Link Your GitHub Account",
                description=f"[Click here to authorize GitHub]({oauth_url})",
                color=0x2ecc71,
            )
            try:
                await interaction.user.send(embed=embed)
                await interaction.followup.send(
                    "📬 I sent you a DM with the auth link!", ephemeral=True
                )
            except discord.Forbidden:
                await interaction.followup.send(
                    "❌ I couldn't send you a DM. Please check your privacy settings.",
                    ephemeral=True,
                )
        except Exception as e:
            await interaction.followup.send(
                f"❌ An error occurred while processing your request: `{type(e).__name__}: {e}`",
                ephemeral=True
            )

    @app_commands.command(name="unauth", description="Unlink your GitHub account from GitBot")
    async def unauth(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            discord_id = str(interaction.user.id)
            result = await self.users_collection.delete_one({"discord_id": discord_id})
            if result.deleted_count:
                await interaction.followup.send("✅ You have been unlinked from GitHub.", ephemeral=True)
            else:
                await interaction.followup.send("ℹ️ You were not linked to any GitHub account.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(
                f"❌ An error occurred while processing your request: `{type(e).__name__}: {e}`",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Auth(bot))

