import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="날씨", description="도시의 현재 날씨 정보를 가져옵니다.(영어로 입력하세요)")
    @app_commands.describe(city="도시 이름을 입력하세요")
    async def get_weather(self, interaction: discord.Interaction, city: str):
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=kr"
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()

                if response.status != 200 or "main" not in data:
                    await interaction.followup.send("날씨 정보를 가져올 수 없습니다. 도시명을 확인해주세요.")
                    return

                weather = data["weather"][0]["description"]
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                humidity = data["main"]["humidity"]

                embed = discord.Embed(title=f"🌤 {city}의 날씨", description=weather, color=discord.Color.blue())
                embed.add_field(name="기온", value=f"{temp}°C")
                embed.add_field(name="체감 온도", value=f"{feels_like}°C")
                embed.add_field(name="습도", value=f"{humidity}%")

                await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Weather(bot))