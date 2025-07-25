import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

class Review(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    async def fetch_github_json(self, url):
        headers = {"Accept": "application/vnd.github+json"}
        async with self.session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return None
            return await resp.json()

    async def generate_review(self, prompt: str):
        async with self.session.post(
            "http://localhost:11434/api/generate",
            json={"model": "mistral", "prompt": prompt, "stream": False}
        ) as resp:
            if resp.status != 200:
                return "⚠️ Error generating review."
            data = await resp.json()
            return data.get("response", "⚠️ No response from model.")

    review = app_commands.Group(name="review", description="AI-powered GitHub repo/PR/issue review")

    @review.command(name="repo", description="Review a GitHub repository")
    @app_commands.describe(repository="Format: owner/repo")
    async def review_repo(self, interaction: discord.Interaction, repository: str):
        await interaction.response.defer()

        url = f"https://api.github.com/repos/{repository}"
        data = await self.fetch_github_json(url)
        if not data:
            return await interaction.followup.send("⚠️ Failed to fetch repo info.")

        prompt = f"""Review this GitHub repository and return a checklist-style evaluation (✅ / ❌) with suggestions:

Name: {data['full_name']}
Description: {data.get('description', 'No description')}
Stars: {data.get('stargazers_count')}
Forks: {data.get('forks_count')}
Open Issues: {data.get('open_issues_count')}
Primary Language: {data.get('language')}
Default Branch: {data.get('default_branch')}
License: {data.get('license', {}).get('name', 'None')}

Checklist and feedback:"""

        ai_response = await self.generate_review(prompt)

        embed = discord.Embed(
            title=f"📦 Review of {data['full_name']}",
            description=ai_response,
            color=discord.Color.green()
        )
        embed.set_footer(text="Powered by Mistral via Ollama")
        await interaction.followup.send(embed=embed)

    @review.command(name="pr", description="Review a GitHub Pull Request")
    @app_commands.describe(repository="Format: owner/repo", number="Pull Request number")
    async def review_pr(self, interaction: discord.Interaction, repository: str, number: int):
        await interaction.response.defer()

        url = f"https://api.github.com/repos/{repository}/pulls/{number}"
        data = await self.fetch_github_json(url)
        if not data:
            return await interaction.followup.send("⚠️ Failed to fetch PR info.")

        prompt = f"""Review this GitHub Pull Request and return a checklist-style evaluation (✅ / ❌) with suggestions:

Repository: {repository}
Title: {data['title']}
Author: {data['user']['login']}
State: {data['state']}
Draft: {data['draft']}
Created At: {data['created_at']}
Changed Files: {data.get('changed_files', 'unknown')}
Additions: {data.get('additions', 'unknown')}
Deletions: {data.get('deletions', 'unknown')}
Body:
{data.get('body', 'No description.')}

Checklist and feedback:"""

        ai_response = await self.generate_review(prompt)

        embed = discord.Embed(
            title=f"🔍 Review of PR #{number} in {repository}",
            description=ai_response,
            color=discord.Color.blue()
        )
        embed.set_footer(text="Powered by Mistral via Ollama")
        await interaction.followup.send(embed=embed)

    @review.command(name="issue", description="Review a GitHub Issue")
    @app_commands.describe(repository="Format: owner/repo", number="Issue number")
    async def review_issue(self, interaction: discord.Interaction, repository: str, number: int):
        await interaction.response.defer()

        url = f"https://api.github.com/repos/{repository}/issues/{number}"
        data = await self.fetch_github_json(url)
        if not data:
            return await interaction.followup.send("⚠️ Failed to fetch issue info.")

        prompt = f"""Analyze this GitHub Issue and return a checklist-style review of clarity, completeness, and reproducibility:

Repository: {repository}
Title: {data['title']}
Author: {data['user']['login']}
State: {data['state']}
Created At: {data['created_at']}
Body:
{data.get('body', 'No description.')}

Checklist and suggestions:"""

        ai_response = await self.generate_review(prompt)

        embed = discord.Embed(
            title=f"🐛 Review of Issue #{number} in {repository}",
            description=ai_response,
            color=discord.Color.orange()
        )
        embed.set_footer(text="Powered by Mistral via Ollama")
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Review(bot))

