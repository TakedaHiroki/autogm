import discord
from discord.ext import commands


intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="!",
    case_insensitive=True,
    intents=intents
)


TOKEN = ''



@bot.event
async def on_ready():
    print('ログインしました')


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    new_channel = await create_private_text_channel(message)
    text = f'{new_channel.mention} を作成しました'
    await message.channel.send(text)

@bot.event
async def create_text_channel(message, channel_name):
    category_id = message.channel.category_id
    category = message.guild.get_channel(category_id)
    new_channel = await category.create_text_channel(name=channel_name)
    return new_channel

@bot.event
async def create_private_text_channel(message):
    category_id = message.channel.category_id
    guild = message.guild
    category = guild.get_channel(category_id)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.get_member(message.author.id): discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    new_channel = await guild.create_text_channel(bot.get_user(message.author.id).display_name, overwrites=overwrites)
    return new_channel

bot.run(TOKEN)