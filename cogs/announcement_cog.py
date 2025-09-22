import discord
from discord.ext import commands
from discord import app_commands, Embed
import io

from utils.data_manager import save_json, ANNOUNCEMENT_CHANNELS_FILE

class AnnouncementCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="start_announcement", description="공지사항 작성을 시작합니다. (메시지 관리 권한 필요)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def start_announcement(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id in self.bot.announcement_drafts:
            await interaction.response.send_message("❗ 이미 공지사항 작성 중입니다. DM을 확인해주세요.", ephemeral=True)
            return

        self.bot.announcement_drafts[user_id] = {'text': '', 'files': [], 'guild_id': interaction.guild.id}
        try:
            await interaction.user.send(
                "```asciidoc\n= 공지사항 작성 시작 =\n---------------------\n"
                "이제 공지사항 내용을 이 DM 채널에 작성해주세요.\n사진/파일 첨부도 가능합니다.\n\n"
                "작성 중 언제든지 '완료'라고 보내면 서버에 전송됩니다.\n'취소'라고 보내면 작성이 중단됩니다.\n```"
            )
            await interaction.response.send_message("✅ 공지사항 작성을 시작합니다. **DM을 확인해주세요!**", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ DM을 보낼 수 없습니다. 디스코드 개인 정보 설정을 확인해주세요.", ephemeral=True)
            self.bot.announcement_drafts.pop(user_id, None)

    @app_commands.command(name="set_announcement_channel", description="이 서버의 공지사항 채널을 설정합니다.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_announcement_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.bot.announcement_channels[interaction.guild.id] = channel.id
        save_data = {str(k): v for k, v in self.bot.announcement_channels.items()}
        save_json(ANNOUNCEMENT_CHANNELS_FILE, save_data)
        await interaction.response.send_message(f"✅ 이 서버의 공지사항 채널이 {channel.mention}으로 설정되었습니다.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not isinstance(message.channel, discord.DMChannel) or message.author.id not in self.bot.announcement_drafts:
            return

        user_id = message.author.id
        draft = self.bot.announcement_drafts[user_id]
        
        if message.content.lower() == "완료":
            await message.channel.send("⏳ 공지사항을 전송하고 있습니다...")
            guild_id = draft['guild_id']
            guild = self.bot.get_guild(guild_id)

            if not guild:
                await message.channel.send("❗ 공지를 보낼 서버를 찾을 수 없습니다. 봇이 해당 서버에 아직 있나요?")
                self.bot.announcement_drafts.pop(user_id, None)
                return

            channel_id = self.bot.announcement_channels.get(guild.id)
            if not channel_id:
                await message.channel.send(f"❗ '{guild.name}' 서버에 공지 채널이 설정되지 않았습니다.")
                self.bot.announcement_drafts.pop(user_id, None)
                return

            channel = self.bot.get_channel(channel_id)
            if not channel:
                await message.channel.send("❗ 설정된 공지 채널을 찾을 수 없습니다. 채널이 삭제되었나요?")
                self.bot.announcement_drafts.pop(user_id, None)
                return

            try:
                files_to_send = [discord.File(io.BytesIO(f_bytes), filename=f"attachment_{i+1}.png") for i, f_bytes in enumerate(draft['files'])]
                
                await channel.send(content=draft['text'] or None, files=files_to_send if files_to_send else None)
                await message.channel.send("✅ 공지사항이 성공적으로 전송되었습니다!")
            except Exception as e:
                await message.channel.send(f"❌ 공지 전송 중 오류 발생: {e}")
            finally:
                self.bot.announcement_drafts.pop(user_id, None)
        
        elif message.content.lower() == "취소":
            self.bot.announcement_drafts.pop(user_id, None)
            await message.channel.send("🚫 공지사항 작성이 취소되었습니다.")
        
        else:
            draft['text'] += message.content + "\n"
            for attachment in message.attachments:
                draft['files'].append(await attachment.read())
            await message.add_reaction("👍")

async def setup(bot: commands.Bot):
    await bot.add_cog(AnnouncementCog(bot))