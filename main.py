import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai
import re

load_dotenv()

BOT_TOKEN = os.environ.get('BOT_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
DEV_ID = int(os.environ.get('DEV_ID', 000)) # 000 빼고 개발자 ID 등록 
SERVER_INVITE_LINK = os.environ.get('SERVER_INVITE_LINK')

if not BOT_TOKEN:
    print("CRITICAL: 봇 토큰이 .env 파일에 없습니다.")
    exit()

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini API 키 설정 완료.")
else:
    print("⚠️ Gemini API 키가 없습니다.")

if SERVER_INVITE_LINK:
    print("✅ 전역 서버 초대 링크 설정 완료.")
else:
    print("⚠️ SERVER_INVITE_LINK가 없습니다.")

from utils.data_manager import load_all_data, PHISHING_URLS, URL_REGEX, INVITE_LINKS

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

bot.reported_users = None
bot.announcement_channels = None
bot.tts_channels = None
bot.autorole_config = None
bot.vrchat_profiles = None
bot.vrchat_config = None
bot.ai_config = None

bot.announcement_drafts = {}
bot.ai_conversations = {}

@bot.event
async def on_ready():
    print(f'로그인: {bot.user.name} (ID: {bot.user.id})')
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("VRChat"))
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)}개의 슬래시 커맨드 동기화 완료.")
    except Exception as e:
        print(f"커맨드 동기화 실패: {e}")
    print('봇 준비 완료.')

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or message.webhook_id:
        return

    if isinstance(message.channel, discord.DMChannel):
        if message.author.id in bot.announcement_drafts:
            return
        try:
            creator = await bot.fetch_user(DEV_ID)
            if creator:
                embed = discord.Embed(
                    title="📥 새로운 DM 도착",
                    description=f"**보낸 사람:** {message.author} ({message.author.id})",
                    color=discord.Color.blue()
                )
                embed.add_field(name="내용", value=message.content, inline=False)
                await creator.send(embed=embed)
        except Exception as e:
            print(f"개발자에게 DM 전달 실패: {e}")

    else:
        if bot.user in message.mentions:
            try:
                creator = await bot.fetch_user(DEV_ID)
                if creator:
                    try:
                        invite = await message.channel.create_invite(
                            max_age=3600, max_uses=1, unique=True,
                            reason=f"봇 멘션 알림 ({message.author})"
                        )
                        invite_link_str = f"**[임시 초대장 바로가기]({invite.url})**"
                    except discord.Forbidden:
                        invite_link_str = "이 채널의 초대장을 만들 권한이 없습니다."
                    except Exception as e:
                        invite_link_str = f"초대장 생성 오류: {e}"

                    embed = discord.Embed(
                        title="🔔 봇 맨션 알림",
                        description=f"**보낸 사람:** {message.author.mention} ({message.author.id})",
                        color=discord.Color.gold()
                    )
                    embed.add_field(name="서버", value=message.guild.name, inline=True)
                    embed.add_field(name="채널", value=message.channel.mention, inline=True)
                    embed.add_field(name="메시지 링크", value=f"[바로가기]({message.jump_url})", inline=False)
                    embed.add_field(name="내용", value=message.content, inline=False)
                    embed.add_field(name="서버 접속", value=invite_link_str, inline=False)
                    await creator.send(embed=embed)
            except Exception as e:
                print(f"개발자에게 멘션 알림 전달 실패: {e}")

        elif message.mentions:
            server_invite_link = INVITE_LINKS.get(str(message.guild.id)) or SERVER_INVITE_LINK
            if server_invite_link:
                users_to_invite = [u for u in message.mentions if not u.bot and u != message.author]
                if users_to_invite:
                    embed = discord.Embed(
                        title=f"💌 {message.guild.name} 서버에 초대되셨어요!",
                        description=f"**{message.author.display_name}**님이 초대했습니다.\n아래 링크로 참여하세요!",
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="서버 참여 링크", value=f"[여기를 클릭하여 참여!]({server_invite_link})")
                    embed.set_footer(text=f"초대자: {message.author.name}")

                    success, fail = [], []
                    for user in users_to_invite:
                        try:
                            await user.send(embed=embed)
                            success.append(user.mention)
                        except discord.Forbidden:
                            fail.append(user.mention)
                        except Exception as e:
                            print(f"{user.name}에게 DM 실패: {e}")
                            fail.append(user.mention)

                    response = []
                    if success:
                        response.append(f"{', '.join(success)}님에게 DM으로 초대장을 보냈어요! 📬")
                    if fail:
                        response.append(f"{', '.join(fail)}님에게는 DM을 보낼 수 없었어요.")
                    if response:
                        await message.channel.send("\n".join(response), delete_after=15)

    found_urls = re.findall(URL_REGEX, message.content)
    for url in found_urls:
        try:
            domain = re.sub(r"https?:\/\/(www\.)?", "", url).split('/')[0].split(':')[0]
            if domain in PHISHING_URLS:
                embed = discord.Embed(
                    title="🚨 위험 감지: 피싱 의심 URL!",
                    description=f"{message.author.mention}님이 보낸 메시지에서 의심 URL이 감지되어 삭제되었습니다.",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed)
                await message.delete()
                break
        except Exception as e:
            print(f"피싱 URL 분석 오류: {e}")

    await bot.process_commands(message)

async def main():
    async with bot:
        load_all_data(bot)
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and filename != '__init__.py':
                try:
                    await bot.load_extension(f'cogs.{filename[:-3]}')
                    print(f'✅ Cog 로드 성공: {filename}')
                except Exception as e:
                    print(f'❌ Cog 로드 실패: {filename} - {e}')
        await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("봇 종료 중...")
