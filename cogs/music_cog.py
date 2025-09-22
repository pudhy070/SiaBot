import discord
from discord.ext import commands
from discord import app_commands, Embed
import yt_dlp
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' 
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'
}

class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues = defaultdict(list)
        self.now_playing = defaultdict(lambda: None)

    async def play_next(self, guild: discord.Guild):
        if self.queues[guild.id] and guild.voice_client:
            song = self.queues[guild.id].pop(0)
            self.now_playing[guild.id] = {**song, 'start_time': datetime.now()}
            try:
                source = await discord.FFmpegOpusAudio.from_probe(song['source'], **FFMPEG_OPTIONS)
                guild.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(guild)) if e is None else print(f'Player error in {guild.name}: {e}'))
                
                embed = Embed(title="🎶 다음 곡 재생", description=f"**[{song['title']}]({song.get('webpage_url', '#')})**", color=discord.Color.green())
                if song.get('thumbnail'):
                    embed.set_thumbnail(url=song.get('thumbnail'))
                embed.set_footer(text=f"신청자: {song['requester'].display_name}")
                await song['channel'].send(embed=embed)
            except Exception as e:
                await song['channel'].send(f"❌ **{song['title']}** 재생 중 오류가 발생했습니다: `{e}`")
                await self.play_next(guild)
        else:
            if guild.id in self.now_playing:
                del self.now_playing[guild.id]
            if guild.voice_client: 
                pass

    @app_commands.command(name="play", description="노래를 재생합니다. (유튜브 링크 또는 검색어)")
    @app_commands.describe(search="재생할 노래의 제목 또는 유튜브 URL")
    async def play(self, interaction: discord.Interaction, search: str):
        if not interaction.user.voice:
            return await interaction.response.send_message("먼저 음성 채널에 입장해주세요.", ephemeral=True)
        
        await interaction.response.defer()
        vc = interaction.guild.voice_client
        if not vc:
            try:
                vc = await interaction.user.voice.channel.connect(self_deaf=True)
            except Exception as e:
                return await interaction.followup.send(f"음성 채널 연결에 실패했습니다: {e}")

        try:
            with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                info = ydl.extract_info(search, download=False)
                if 'entries' in info:
                    song_info = info['entries'][0]
                else:
                    song_info = info
        except Exception as e:
            return await interaction.followup.send(f"❌ 노래 정보 로딩 중 오류가 발생했습니다: `{e}`")

        if not song_info:
             return await interaction.followup.send("노래를 찾을 수 없습니다.", ephemeral=True)
        
        song = {
            'source': song_info['url'], 
            'webpage_url': song_info.get('webpage_url'), 
            'title': song_info.get('title', '제목 없음'),
            'thumbnail': song_info.get('thumbnail'),
            'duration': song_info.get('duration', 0), 
            'requester': interaction.user, 
            'channel': interaction.channel
        }
        
        self.queues[interaction.guild.id].append(song)
        if not vc.is_playing() and not vc.is_paused():
            await interaction.followup.send(f"🎶 **{song['title']}** 재생을 시작합니다.")
            await self.play_next(interaction.guild)
        else:
            embed = Embed(title="✅ 대기열에 추가", description=f"**[{song['title']}]({song.get('webpage_url')})**", color=discord.Color.blue())
            if song.get('thumbnail'):
                embed.set_thumbnail(url=song.get('thumbnail'))
            await interaction.followup.send(embed=embed)
            
    @app_commands.command(name="join", description="봇을 현재 음성 채널에 참여시킵니다.")
    async def join(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            return await interaction.response.send_message("먼저 음성 채널에 입장해주세요.", ephemeral=True)
        
        if interaction.guild.voice_client:
            return await interaction.response.send_message("봇이 이미 음성 채널에 있습니다.", ephemeral=True)

        try:
            await interaction.user.voice.channel.connect(self_deaf=True)
            await interaction.response.send_message("✅ 음성 채널에 접속했습니다.")
        except Exception as e:
            await interaction.response.send_message(f"❌ 음성 채널 연결 실패: `{e}`")

    @app_commands.command(name="leave", description="봇을 음성 채널에서 내보냅니다.")
    async def leave(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc:
            return await interaction.response.send_message("봇이 음성 채널에 없습니다.", ephemeral=True)
        
        self.queues[interaction.guild.id].clear()
        if interaction.guild.id in self.now_playing:
            del self.now_playing[interaction.guild.id]
            
        await vc.disconnect()
        await interaction.response.send_message("👋 음성 채널에서 퇴장했습니다.")

    @app_commands.command(name="pause", description="현재 재생 중인 노래를 일시정지합니다.")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ 노래를 일시정지했습니다.")
        else:
            await interaction.response.send_message("재생 중인 노래가 없거나 이미 일시정지 상태입니다.", ephemeral=True)

    @app_commands.command(name="resume", description="일시정지된 노래를 다시 재생합니다.")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ 노래를 다시 재생합니다.")
        else:
            await interaction.response.send_message("일시정지된 노래가 없습니다.", ephemeral=True)

    @app_commands.command(name="skip", description="현재 재생 중인 노래를 건너뜁니다.")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            await interaction.response.send_message("⏭️ 노래를 건너뛰었습니다.")
        else:
            await interaction.response.send_message("재생 중인 노래가 없습니다.", ephemeral=True)

    @app_commands.command(name="queue", description="현재 재생 대기열을 보여줍니다.")
    async def queue(self, interaction: discord.Interaction):
        gid = interaction.guild.id
        queue = self.queues[gid]
        
        if not self.now_playing.get(gid) and not queue:
             return await interaction.response.send_message("대기열에 노래가 없습니다.", ephemeral=True)
        
        embed = Embed(title="🎵 재생 대기열", color=discord.Color.purple())
        
        if self.now_playing.get(gid):
            current_song = self.now_playing[gid]
            embed.description = f"**💿 현재 재생 중**\n[{current_song['title']}]({current_song.get('webpage_url')})\n\n"
        else:
            embed.description = ""

        if queue:
            queue_list = "\n".join(f"`{i+1}`. {song['title']}" for i, song in enumerate(queue[:10]))
            if len(queue) > 10:
                queue_list += f"\n... 외 {len(queue) - 10}곡"
            embed.description += f"**⬇️ 다음 곡**\n{queue_list}"
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="nowplaying", description="현재 재생 중인 노래의 정보를 보여줍니다.")
    async def nowplaying(self, interaction: discord.Interaction):
        gid = interaction.guild.id
        song = self.now_playing.get(gid)
        vc = interaction.guild.voice_client

        if not song or not vc or (not vc.is_playing() and not vc.is_paused()):
            return await interaction.response.send_message("현재 재생 중인 노래가 없습니다.", ephemeral=True)
        
        elapsed = (datetime.now() - song['start_time']).total_seconds()
        duration = song.get('duration', 0)
        
        if duration > 0:
            progress = int((elapsed / duration) * 20) if duration > 0 else 0
            if progress > 19:
                progress = 19
            p_bar = "─" * progress + "🔵" + "─" * (19 - progress)
            duration_str = str(timedelta(seconds=int(duration)))
            elapsed_str = str(timedelta(seconds=int(elapsed)))
        else:
            p_bar = "실시간 스트리밍"
            duration_str = "N/A"
            elapsed_str = str(timedelta(seconds=int(elapsed)))

        embed = Embed(title="💿 현재 재생 중", description=f"**[{song['title']}]({song.get('webpage_url', '#')})**", color=discord.Color.gold())
        if song.get('thumbnail'):
            embed.set_thumbnail(url=song.get('thumbnail'))
        embed.add_field(name="신청자", value=song['requester'].mention, inline=True)
        embed.add_field(name="재생 시간", value=f"`{elapsed_str} / {duration_str}`", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="진행률", value=f"`{p_bar}`", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="np", description="현재 재생 중인 노래 정보를 보여줍니다. (nowplaying 단축)")
    async def np_alias(self, interaction: discord.Interaction):
        await self.nowplaying(interaction)

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))