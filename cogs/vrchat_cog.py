import discord
from discord.ext import commands
from discord import app_commands, Embed, ui

from utils.data_manager import save_json, VRCHAT_CONFIG_FILE, VRCHAT_PROFILES_FILE

class VRChatApprovalView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def handle_decision(self, interaction: discord.Interaction, decision: str, bot: commands.Bot):
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message("이 버튼은 역할 관리 권한이 있는 사람만 누를 수 있습니다.", ephemeral=True)
            
        original_embed = interaction.message.embeds[0]
        try:
            applicant_id = int(original_embed.footer.text.split("ID: ")[1])
            profile_link = original_embed.fields[0].value
        except (IndexError, ValueError):
            return await interaction.response.send_message("신청 정보를 분석하는 데 실패했습니다.", ephemeral=True)

        applicant = interaction.guild.get_member(applicant_id)
        if not applicant:
            await interaction.response.send_message("신청자를 서버에서 찾을 수 없습니다.", ephemeral=True)
            await interaction.message.edit(content="신청자가 서버를 나갔습니다.", embed=None, view=None)
            return

        guild_id_str = str(interaction.guild.id)
        config = bot.vrchat_config.get(guild_id_str, {})
        role_id = config.get('role_id')
        role_to_grant = interaction.guild.get_role(role_id) if role_id else None

        new_embed = Embed(color=discord.Color.green() if decision == "approve" else discord.Color.red())
        new_embed.set_footer(text=f"처리자: {interaction.user.name} | 신청자 ID: {applicant_id}")
        new_embed.add_field(name="프로필 링크", value=profile_link, inline=False)
        
        dm_message = ""
        if decision == "approve":

            bot.vrchat_profiles[str(applicant_id)] = profile_link
            save_json(VRCHAT_PROFILES_FILE, bot.vrchat_profiles)
            
            new_embed.title = "✅ VRChat 프로필 승인됨"
            new_embed.description=f"{applicant.mention}님의 프로필이 승인되었습니다."
            dm_message = f"🎉 **{interaction.guild.name}** 서버의 VRChat 프로필 인증이 **승인**되었습니다!"
            
            if role_to_grant:
                try:
                    await applicant.add_roles(role_to_grant)
                    dm_message += f"\n`{role_to_grant.name}` 역할이 부여되었습니다."
                except Exception as e:
                    print(f"VRChat 역할 부여 실패: {e}")
                    await interaction.channel.send(f"⚠️ {applicant.mention}님에게 역할 부여 중 오류가 발생했습니다.")
            
        else:
            new_embed.title = "❌ VRChat 프로필 반려됨"
            new_embed.description=f"{applicant.mention}님의 프로필이 반려되었습니다."
            dm_message = f"😢 **{interaction.guild.name}** 서버의 VRChat 프로필 인증이 **반려**되었습니다."
        
        self.clear_items()
        await interaction.message.edit(embed=new_embed, view=self)
        await interaction.response.send_message(f"{applicant.mention}님의 신청을 '{decision}' 처리했습니다.", ephemeral=True)
        
        try:
            await applicant.send(dm_message)
        except discord.Forbidden:
            pass

    @ui.button(label="승인", style=discord.ButtonStyle.green, custom_id="vrchat_approve_button_persistent")
    async def approve_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_decision(interaction, "approve", interaction.client)

    @ui.button(label="반려", style=discord.ButtonStyle.red, custom_id="vrchat_deny_button_persistent")
    async def deny_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_decision(interaction, "deny", interaction.client)


class VRChatCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(VRChatApprovalView())

    @app_commands.command(name="vrchat_setup", description="VRChat 인증 시스템을 설정합니다. (관리자용)")
    @app_commands.checks.has_permissions(administrator=True)
    async def vrchat_setup(self, interaction: discord.Interaction, approval_channel: discord.TextChannel, role_to_grant: discord.Role):
        guild_id_str = str(interaction.guild.id)
        self.bot.vrchat_config[guild_id_str] = {
            'approval_channel_id': approval_channel.id,
            'role_id': role_to_grant.id
        }
        save_json(VRCHAT_CONFIG_FILE, self.bot.vrchat_config)
        await interaction.response.send_message(f"✅ VRChat 인증 설정 완료!\n- 승인 채널: {approval_channel.mention}\n- 부여 역할: {role_to_grant.mention}", ephemeral=True)

    @app_commands.command(name="vrchat_apply", description="VRChat 프로필 링크를 제출하여 인증을 신청합니다.")
    async def vrchat_apply(self, interaction: discord.Interaction, profile_link: str):
        if "vrchat.com/home/user/" not in profile_link:
            return await interaction.response.send_message("올바른 VRChat 프로필 링크가 아닙니다. `https://vrchat.com/home/user/...` 형식이어야 합니다.", ephemeral=True)

        guild_id_str = str(interaction.guild.id)
        config = self.bot.vrchat_config.get(guild_id_str)
        if not config:
            return await interaction.response.send_message("VRChat 인증 시스템이 이 서버에 설정되지 않았습니다.", ephemeral=True)
        
        approval_channel = self.bot.get_channel(config['approval_channel_id'])
        if not approval_channel:
            return await interaction.response.send_message("설정된 승인 채널을 찾을 수 없습니다. 관리자에게 문의하세요.", ephemeral=True)
            
        embed = Embed(title="📝 VRChat 프로필 인증 신청", description=f"**신청자:** {interaction.user.mention}", color=discord.Color.yellow())
        embed.add_field(name="프로필 링크", value=profile_link, inline=False)
        embed.set_footer(text=f"신청자 ID: {interaction.user.id}")
        
        await approval_channel.send(embed=embed, view=VRChatApprovalView())
        await interaction.response.send_message("✅ 프로필 인증 신청이 제출되었습니다. 관리자의 승인을 기다려주세요.", ephemeral=True)

    @app_commands.command(name="view_profile", description="유저의 저장된 VRChat 프로필 링크를 확인합니다.")
    async def view_profile(self, interaction: discord.Interaction, user: discord.Member):
        profile_link = self.bot.vrchat_profiles.get(str(user.id))
        if profile_link:
            embed = Embed(title=f"👤 {user.display_name}님의 VRChat 프로필", description=f"[{profile_link}]({profile_link})", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"{user.display_name}님은 등록된 VRChat 프로필이 없습니다.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(VRChatCog(bot))