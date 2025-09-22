import discord
from discord import app_commands
from discord.ext import commands
from utils.data_manager import INVITE_LINKS, save_invite_links

class ServerManagement(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="초대링크설정", description="개발자 알림에 사용할 서버의 영구 초대 링크를 설정합니다.")
    @app_commands.describe(link="서버의 영구 초대 링크 (예: https://discord.gg/your-invite)")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_invite_link(self, interaction: discord.Interaction, link: str):
        if not ("discord.gg/" in link or "discord.com/invite/" in link):
            await interaction.response.send_message("유효한 디스코드 초대 링크 형식이 아닙니다. 다시 확인해주세요.", ephemeral=True)
            return

        guild_id = str(interaction.guild.id)
        INVITE_LINKS[guild_id] = link
        save_invite_links()

        embed = discord.Embed(
            title="✅ 초대 링크 설정 완료",
            description=f"이 서버의 알림용 초대 링크가 아래와 같이 설정되었습니다.\n\n**{link}**",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @set_invite_link.error
    async def set_invite_link_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("이 명령어를 사용하려면 서버 관리자 권한이 필요합니다.", ephemeral=True)
        else:
            await interaction.response.send_message(f"오류가 발생했습니다: {error}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ServerManagement(bot))