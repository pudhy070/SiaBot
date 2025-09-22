import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

class News(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="뉴스", description="키워드에 관련된 최신 뉴스를 가져옵니다.")
    @app_commands.describe(keyword="뉴스 키워드 (예: AI)")
    async def fetch_news(self, interaction: discord.Interaction, keyword: str = "AI"):
        url = f"https://newsapi.org/v2/everything?q={keyword}&sortBy=publishedAt&language=ko&pageSize=3&apiKey={NEWS_API_KEY}"
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()

                if response.status != 200 or not data.get("articles"):
                    await interaction.followup.send("뉴스를 가져올 수 없습니다.")
                    return

                embed = discord.Embed(title=f"📰 '{keyword}' 관련 최신 뉴스", color=discord.Color.orange())
                for article in data["articles"]:
                    embed.add_field(
                        name=article["title"],
                        value=f"[기사 보기]({article['url']})",
                        inline=False
                    )
                await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(News(bot))