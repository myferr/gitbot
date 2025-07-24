import discord
from discord import app_commands
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient
import httpx

class Me(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
        self.users_collection = self.mongo_client.gitbot.users

    @app_commands.command(name="me", description="Show your GitHub authentication status and profile info")
    async def me(self, interaction: discord.Interaction):
        discord_id = str(interaction.user.id)
        user = await self.users_collection.find_one({"discord_id": discord_id})

        if not user:
            await interaction.response.send_message(
                "❌ You are not linked to any GitHub account. Use `/auth` to link your account.", ephemeral=True
            )
            return

        token = user.get("token")
        github_user = user.get("github_user")

        if not token or not github_user:
            await interaction.response.send_message(
                "⚠️ Your GitHub authentication info seems incomplete. Please re-authenticate with `/auth`.", ephemeral=True
            )
            return

        headers = {"Authorization": f"token {token}"}
        async with httpx.AsyncClient() as client:
            res = await client.get("https://api.github.com/user", headers=headers)
            if res.status_code != 200:
                await interaction.response.send_message(
                    "⚠️ Failed to fetch GitHub profile. Your token may be invalid. Please re-authenticate.", ephemeral=True
                )
                return

            data = res.json()
            embed = discord.Embed(
                title=f"GitHub Profile — {data.get('login')}",
                url=data.get("html_url"),
                color=0x2ecc71,
                description=data.get("bio") or "No bio"
            )
            embed.set_thumbnail(url=data.get("avatar_url"))
            embed.add_field(name="Name", value=data.get("name") or "N/A", inline=True)
            embed.add_field(name="Public Repos", value=str(data.get("public_repos")), inline=True)
            embed.add_field(name="Followers", value=str(data.get("followers")), inline=True)
            embed.add_field(name="Following", value=str(data.get("following")), inline=True)
            embed.add_field(name="Location", value=data.get("location") or "N/A", inline=True)
            embed.add_field(name="Email", value=data.get("email") or "N/A", inline=True)

            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Me(bot))

