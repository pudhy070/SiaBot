import discord
from discord.ext import commands
from discord import Embed
import re
import google.generativeai as genai
from utils.data_manager import save_json, AI_CONFIG_FILE

class AICog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='set_ai_channel')
    @commands.has_permissions(administrator=True)
    async def set_ai_channel_command(self, ctx: commands.Context):
        guild_id_str = str(ctx.guild.id)
        if guild_id_str not in self.bot.ai_config:
            self.bot.ai_config[guild_id_str] = {}
        self.bot.ai_config[guild_id_str]['channel_id'] = ctx.channel.id
        save_json(AI_CONFIG_FILE, self.bot.ai_config)
        await ctx.reply(f"✅ 이 채널을 AI 대화 채널로 설정했어요. 저를 멘션해서 대화를 시작해보세요!")

    @commands.command(name='set_ai_personality')
    @commands.has_permissions(administrator=True)
    async def set_ai_personality_command(self, ctx: commands.Context, *, personality: str):
        guild_id_str = str(ctx.guild.id)
        if guild_id_str not in self.bot.ai_config:
            self.bot.ai_config[guild_id_str] = {}
        self.bot.ai_config[guild_id_str]['personality'] = personality
        save_json(AI_CONFIG_FILE, self.bot.ai_config)
        
        if ctx.channel.id in self.bot.ai_conversations:
            del self.bot.ai_conversations[ctx.channel.id]
        await ctx.reply(f"✅ AI의 성격을 설정했어요. 새로운 대화를 시작할게요.")

    @commands.command(name='reset_ai_personality')
    @commands.has_permissions(administrator=True)
    async def reset_ai_personality_command(self, ctx: commands.Context):
        guild_id_str = str(ctx.guild.id)
        if guild_id_str in self.bot.ai_config and 'personality' in self.bot.ai_config[guild_id_str]:
            del self.bot.ai_config[guild_id_str]['personality']
            save_json(AI_CONFIG_FILE, self.bot.ai_config)
            if ctx.channel.id in self.bot.ai_conversations:
                del self.bot.ai_conversations[ctx.channel.id]
            await ctx.reply("✅ AI의 성격을 기본값으로 초기화했어요.")
        else:
            await ctx.reply("설정된 AI 성격이 없어요.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild_id_str = str(message.guild.id)
        config = self.bot.ai_config.get(guild_id_str, {})
        
        if config.get('channel_id') == message.channel.id and self.bot.user.mentioned_in(message):
            async with message.channel.typing():
                try:
                    personality = config.get('personality', 
                                             "") # 여기 공백에 기본 성격 등록
                    
                    model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest', system_instruction=personality)

                    conversation_history = self.bot.ai_conversations.get(message.channel.id, [])
                    if len(conversation_history) > 10:
                        conversation_history = conversation_history[-10:]

                    chat = model.start_chat(history=conversation_history)
                    clean_content = re.sub(r'<@!?(\d+)>', '', message.content).strip()
                    response = await chat.send_message_async(clean_content)
                    ai_response = response.text

                    conversation_history.append({'role': 'user', 'parts': [clean_content]})
                    conversation_history.append({'role': 'model', 'parts': [ai_response]})
                    self.bot.ai_conversations[message.channel.id] = conversation_history
                    
                    if len(ai_response) > 2000:
                        for i in range(0, len(ai_response), 2000):
                            await message.reply(ai_response[i:i+2000])
                    else:
                        await message.reply(ai_response)

                except Exception as e:
                    await message.reply(f"죄송해요, AI 답변 생성 중 오류가 발생했어요: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(AICog(bot))