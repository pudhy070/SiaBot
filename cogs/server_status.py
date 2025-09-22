import discord
from discord import app_commands
from discord.ext import commands

class ServerStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="서버통계", description="서버의 전체 통계 정보를 보여줍니다.")
    async def server_stats(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("서버 내에서만 사용할 수 있습니다.", ephemeral=True)
            return

        total_members = guild.member_count

        online_members = 0
        offline_members = 0
        for member in guild.members:
            if member.bot:
                continue
            if member.status == discord.Status.offline:
                offline_members += 1
            else:
                online_members += 1

        try:
            bans = await guild.bans()
            banned_users = len(bans)
        except discord.Forbidden:
            banned_users = "권한 없음 🔒"

        embed = discord.Embed(title=f"{guild.name} 서버 통계", color=discord.Color.green())
        embed.add_field(name="총 멤버 수", value=str(total_members), inline=False)
        embed.add_field(name="온라인 유저 수", value=str(online_members), inline=True)
        embed.add_field(name="오프라인 유저 수", value=str(offline_members), inline=True)
        embed.add_field(name="차단된 유저 수", value=str(banned_users), inline=False)

        embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerStats(bot))