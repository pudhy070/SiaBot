import discord
from discord.ext import commands
from discord import app_commands, Embed

from utils.data_manager import save_json, AUTOROLE_FILE, REPORTED_USERS_FILE, TTS_CHANNELS_FILE

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id_str = str(member.guild.id)
        if guild_id_str in self.bot.autorole_config:
            role_id = self.bot.autorole_config[guild_id_str]
            role = member.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role)
                    print(f"{member.guild.name} 서버에서 {member.name}에게 '{role.name}' 역할을 부여했습니다.")
                except discord.Forbidden:
                    print(f"권한 부족: {member.guild.name} 서버에서 역할을 부여할 수 없습니다.")
                except Exception as e:
                    print(f"자동 역할 부여 중 오류 발생: {e}")

    @commands.command(name='상태')
    @commands.has_permissions(administrator=True)
    async def change_status_command(self, ctx, *, message: str):
        try:
            activity = discord.Game(name=message)
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
            await ctx.send(f'봇의 상태 메시지를 "{message}"(으)로 변경했어요!')
        except Exception as e:
            await ctx.send(f"상태 변경 중 오류가 발생했어요: {e}")

    @app_commands.command(name="clear", description="채널의 메시지를 지정한 개수만큼 삭제합니다.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        if not 1 <= amount <= 1000:
            return await interaction.response.send_message("1에서 1000 사이의 값을 입력해주세요.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"✅ 메시지 {len(deleted)}개를 삭제했습니다.", ephemeral=True)

    @app_commands.command(name="set_join_role", description="신규 유저에게 자동으로 부여할 역할을 설정합니다.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_join_role(self, interaction: discord.Interaction, role: discord.Role):
        guild_id_str = str(interaction.guild.id)
        self.bot.autorole_config[guild_id_str] = role.id
        save_json(AUTOROLE_FILE, self.bot.autorole_config) 
        await interaction.response.send_message(f"✅ 신규 유저 자동 역할이 `{role.name}`(으)로 설정되었습니다.")

    @app_commands.command(name="unset_join_role", description="자동 역할 부여 설정을 해제합니다.")
    @app_commands.checks.has_permissions(administrator=True)
    async def unset_join_role(self, interaction: discord.Interaction):
        guild_id_str = str(interaction.guild.id)
        if guild_id_str in self.bot.autorole_config:
            del self.bot.autorole_config[guild_id_str]
            save_json(AUTOROLE_FILE, self.bot.autorole_config)
            await interaction.response.send_message("✅ 자동 역할 부여 설정이 해제되었습니다.")
        else:
            await interaction.response.send_message("설정된 자동 역할이 없습니다.", ephemeral=True)
            
    @app_commands.command(name="report", description="유해 사용자를 신고합니다.")
    async def report(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        user_id_str = str(user.id)
        self.bot.reported_users[user_id_str]['count'] += 1
        self.bot.reported_users[user_id_str]['reasons'].append(f"신고자: {interaction.user.name}, 사유: {reason}")
        save_json(REPORTED_USERS_FILE, self.bot.reported_users)
        
        count = self.bot.reported_users[user_id_str]['count']
        if count >= 3:
            report_message = (f"**🚨 경고: 유해 사용자 신고 누적! 🚨**\n"
                              f"사용자: {user.mention} ({user.id})\n"
                              f"**누적 신고 횟수: {count}**\n"
                              f"**최근 사유**: {reason}")
            await interaction.response.send_message(report_message, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
        else:
            await interaction.response.send_message(f"✅ {user.mention}님에 대한 신고가 접수되었습니다. (현재 신고 횟수: {count})", ephemeral=True)

    @app_commands.command(name="set_tts_channel", description="TTS 전용 채널을 설정합니다. (아직 기능 구현 중)")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_tts_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.bot.tts_channels[str(interaction.guild.id)] = channel.id
        save_json(TTS_CHANNELS_FILE, self.bot.tts_channels)
        await interaction.response.send_message(f"✅ {channel.mention} 채널이 TTS 전용 채널로 설정되었습니다.")

    @app_commands.command(name="unset_tts_channel", description="TTS 채널 설정을 해제합니다.")
    @app_commands.checks.has_permissions(administrator=True)
    async def unset_tts_channel(self, interaction: discord.Interaction):
        guild_id_str = str(interaction.guild.id)
        if guild_id_str in self.bot.tts_channels:
            del self.bot.tts_channels[guild_id_str]
            save_json(TTS_CHANNELS_FILE, self.bot.tts_channels)
            await interaction.response.send_message("✅ TTS 채널 설정이 해제되었습니다.")
        else:
            await interaction.response.send_message("설정된 TTS 채널이 없습니다.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))