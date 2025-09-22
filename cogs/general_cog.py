import discord
from discord.ext import commands
from discord import app_commands, Embed
from datetime import timedelta, datetime

DEV_ID = 500510047265357825 # 예시 개발자 ID 꼭 변경 하세요

class GeneralCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def show_developer_info(self, interaction: discord.Interaction):
        try:
            dev_user = await self.bot.fetch_user(DEV_ID)
            embed = Embed(title="👨‍💻 개발자 정보", description="안녕하세요! 저는 이 봇을 개발한 Sia 입니다", color=0x7289DA) # 여기에 정보 변경
            if dev_user.avatar:
                embed.set_thumbnail(url=dev_user.avatar.url)
            embed.add_field(name="닉네임", value="「 Sia 」", inline=True) # 변경 
            embed.add_field(name="디스코드 태그", value=f"`{dev_user}`", inline=True) 
            embed.add_field(name="연락처", value="버그 제보나 문의는 DM으로 보내주세요.", inline=False)
            embed.set_footer(text="봇을 이용해주셔서 감사합니다!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"개발자 정보 표시 중 오류: {e}")
            await interaction.response.send_message("개발자 정보를 가져오는 데 실패했습니다.", ephemeral=True)

    @app_commands.command(name="help", description="봇의 모든 명령어 목록을 보여줍니다.")
    async def help_command(self, interaction: discord.Interaction):
        embed = Embed(title="📘 봇 도움말", description="봇이 제공하는 모든 기능 목록입니다.", color=discord.Color.blurple())
        embed.add_field(name="🎵 음악 기능", value="`/play`, `/pause`, `/resume`, `/skip`, `/queue`, `/nowplaying`, `/join`, `/leave`", inline=False)
        embed.add_field(name="👤 사용자 기능", value="`/myprofile`, `/report`, `/vrchat_apply`, `/view_profile`, `/개발자정보`", inline=False)
        embed.add_field(name="📢 공지 기능", value="`/start_announcement`, `/send_announcement_direct`", inline=False)
        embed.add_field(name="⚙️ 서버 관리", value="`!상태`, `/clear`, `/set_join_role`, `/set_announcement_channel`, `/vrchat_setup`", inline=False)
        embed.add_field(name="💬 AI 기능", value="`!set_ai_channel`, `!set_ai_personality`\n(설정 후 채널에서 봇을 멘션하여 대화)", inline=False)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="개발자정보", description="이 봇의 개발자 정보를 보여줍니다.")
    async def developer_slash_command(self, interaction: discord.Interaction):
        await self.show_developer_info(interaction)

    @commands.command(name='개발자정보')
    async def dev_info_command(self, ctx: commands.Context):
        class MockInteraction:
            def __init__(self, message):
                self.message = message
            @property
            def response(self):
                return self.message.channel
        
        mock_interaction = MockInteraction(ctx.message)
        dev_user = await self.bot.fetch_user(DEV_ID)
        embed = Embed(title="👨‍💻 개발자 정보", description="안녕하세요! 이 봇을 만들고 이상한걸 개발하는 개발자입니다.", color=0x7289DA)
        if dev_user.avatar:
            embed.set_thumbnail(url=dev_user.avatar.url)
        embed.add_field(name="닉네임", value="「 Sia 」", inline=True)
        embed.add_field(name="디스코드 태그", value=f"`{dev_user}`", inline=True)
        embed.add_field(name="연락처", value="버그 제보나 문의는 DM으로 보내주세요.", inline=False)
        embed.set_footer(text="봇을 이용해주셔서 감사합니다!")
        await ctx.send(embed=embed)


    @app_commands.command(name="myprofile", description="자신의 프로필 카드를 확인합니다.")
    @app_commands.describe(member="프로필을 볼 멤버 (선택사항)")
    async def myprofile(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member = interaction.user
        embed = Embed(title=f"🎉 {member.display_name}님의 프로필", description=f"{member.mention}님의 프로필 카드!", color=0xFFD700)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"{member.guild.name} 서버")
        embed.add_field(name="👤 사용자 이름", value=member.name, inline=True)
        embed.add_field(name="🗓️ 서버 가입", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="📅 계정 생성", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
        await interaction.response.send_message(embed=embed)
        
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id_str = str(member.guild.id)
        if guild_id_str in self.bot.autorole_config:
            role_id = self.bot.autorole_config[guild_id_str]
            role = member.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role, reason="자동 역할 부여")
                except Exception as e:
                    print(f"자동 역할 부여 실패 ({member.guild.name}): {e}")
        embed = Embed(title=f"🎉 **{member.name}님의 프로필** 🎉", description=f"{member.mention}님이 서버에 가입하셨습니다!", color=0xFFD700)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"{member.guild.name} 서버에 오신 것을 환영합니다!")
        try:
            await member.send(embed=embed)
        except discord.errors.Forbidden:
            print(f"{member.name}에게 DM을 보낼 수 없습니다.")

async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralCog(bot))