import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os
from urllib.parse import quote

RIOT_API_KEY = os.getenv("RIOT_API_KEY")

class LoLStats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.base_url = "https://kr.api.riotgames.com"
        if not RIOT_API_KEY:
            print("🚨 RIOT_API_KEY가 로드되지 않았습니다! .env 파일을 확인하세요.")

    async def fetch_data(self, session, url):
        headers = {"X-Riot-Token": RIOT_API_KEY}
        async with session.get(url, headers=headers) as response:
            if response.status == 403:
                return None, 403
            return await response.json(), response.status

    @app_commands.command(name="롤전적", description="소환사의 롤 랭크 전적을 가져옵니다.")
    @app_commands.describe(summoner_name="소환사 이름을 입력하세요.")
    async def get_lol_stats(self, interaction: discord.Interaction, summoner_name: str):
        if not RIOT_API_KEY:
            await interaction.response.send_message("❌ 봇 설정에 오류가 발생했습니다. (API 키 없음)")
            return
            
        await interaction.response.defer()

        encoded_name = quote(summoner_name)
        
        async with aiohttp.ClientSession() as session:
            summoner_url = f"{self.base_url}/lol/summoner/v4/summoners/by-name/{encoded_name}"
            summoner_data, status_code = await self.fetch_data(session, summoner_url)

            if status_code == 403:
                print("❌ Riot API Key가 만료되었거나 잘못되었습니다.")
                await interaction.followup.send("❌ Riot API 인증에 실패했습니다. API 키가 만료되었을 수 있습니다.")
                return

            if not summoner_data or "id" not in summoner_data:
                print(f"❌ 소환사 응답 오류: {summoner_data}")
                await interaction.followup.send(f"❌ 소환사 '{summoner_name}'을(를) 찾을 수 없습니다.")
                return

            summoner_id = summoner_data['id']
            ranked_url = f"{self.base_url}/lol/league/v4/entries/by-summoner/{summoner_id}"
            ranked_data, _ = await self.fetch_data(session, ranked_url)

            embed = discord.Embed(
                title=f"RIOT",
                description=f"**{summoner_name}**님의 롤 전적",
                color=discord.Color.gold()
            )
            
            profile_icon_id = summoner_data['profileIconId']
            icon_url = f"http://ddragon.leagueoflegends.com/cdn/14.9.1/img/profileicon/{profile_icon_id}.png"
            embed.set_thumbnail(url=icon_url)

            if ranked_data:
                solo_rank_info = None
                flex_rank_info = None
                
                for queue in ranked_data:
                    if queue["queueType"] == "RANKED_SOLO_5x5":
                        solo_rank_info = queue
                    elif queue["queueType"] == "RANKED_FLEX_SR":
                        flex_rank_info = queue

                if solo_rank_info:
                    win_rate = round((solo_rank_info['wins'] / (solo_rank_info['wins'] + solo_rank_info['losses'])) * 100, 2)
                    embed.add_field(
                        name="솔로랭크",
                        value=f"**{solo_rank_info['tier']} {solo_rank_info['rank']}** - {solo_rank_info['leaguePoints']} LP\n"
                              f"승: {solo_rank_info['wins']} / 패: {solo_rank_info['losses']} (승률: {win_rate}%)",
                        inline=False
                    )

                if flex_rank_info:
                    win_rate = round((flex_rank_info['wins'] / (flex_rank_info['wins'] + flex_rank_info['losses'])) * 100, 2)
                    embed.add_field(
                        name="자유랭크",
                        value=f"**{flex_rank_info['tier']} {flex_rank_info['rank']}** - {flex_rank_info['leaguePoints']} LP\n"
                              f"승: {flex_rank_info['wins']} / 패: {flex_rank_info['losses']} (승률: {win_rate}%)",
                        inline=False
                    )
                
                if not solo_rank_info and not flex_rank_info:
                    embed.add_field(name="랭크 정보", value="솔로/자유 랭크 정보가 없습니다.", inline=False)

            else:
                embed.add_field(name="랭크 정보", value="배치고사를 보지 않은 언랭크 유저입니다.", inline=False)

            embed.set_footer(text=f"요청자: {interaction.user.display_name}")
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LoLStats(bot))