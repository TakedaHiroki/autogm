import asyncio

import discord
from discord.ext import commands

from scheduler import Scheduler
from classes.bite import Bite
from classes.guard import Guard
from classes.vote import Vote


intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix='!',
    case_insensitive=True,
    intents=intents
)


TOKEN = ''

participants = []
survivors = []
bite = Bite()
guard = Guard()
vote = Vote(survivors)


def get_data(message):
    command = message.content
    data_table = {
        '/members': message.guild.members,
        '/roles': message.guild.roles,
        '/text_channels': message.guild.text_channels,
        '/voice_channels': message.guild.voice_channels,
        '/category_channels': message.guild.categories,
    }
    return data_table.get(command, '無効なコマンドです')

@bot.event
async def on_ready():
    print('ログインしました')


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    elif message.content.startswith('噛み→'):
        cmd, dst = message.content.split('→')
        if cmd == '噛み' and dst in survivors:
            bite.push(message.author.name, dst)
            await message.channel.send(bite.src+'さんは'+bite.dst+'さんを噛みました')
        else:
            await message.channel.send('もう一度やり直してください')

    elif message.content.startswith('護衛→'):
        cmd, dst = message.content.split('→')
        if cmd == '護衛' and dst in survivors:
            guard.push(message.author.name, dst)
            await message.channel.send(guard.src+'さんは'+guard.dst+'さんを護衛しました')
        else:
            await message.channel.send('もう一度やり直してください')
            
    elif message.content.startswith('投票→'):
        cmd, dst = message.content.split('→')
        if cmd == '投票' and dst in survivors:
            vote.push(message.author.name, dst)
            await message.channel.send('あなたは'+vote.result[message.author.name]+'さんに投票しました')
        else:
            await message.channel.send('もう一度やり直してください')
    
    elif message.content.upper() == '/INIT':
        for channel in message.guild.channels:
            if channel.name == 'log':
                await channel.delete()
            elif channel.name == 'times':
                await channel.delete()
            elif channel.name == '下界':
                await channel.delete()
            elif channel.name == '霊界':
                await channel.delete()
        new_channel = await create_log_channel(message.guild, 'log')
        text = f'{new_channel.mention} を作成しました'
        await message.channel.send(text)
        new_channel = await create_log_channel(message.guild, 'times')
        text = f'{new_channel.mention} を作成しました'
        await message.channel.send(text)
        new_channel = await create_voice_channel(message.guild, '下界')
        text = f'{new_channel.mention} を作成しました'
        await message.channel.send(text)
        new_channel = await create_voice_channel(message.guild, '霊界')
        text = f'{new_channel.mention} を作成しました'
        await message.channel.send(text)

    elif message.content.upper().startswith('/JOIN'):
        for mention in message.mentions:
            participants.append(mention.name)
            survivors.append(mention.name)
        text = f"{' '.join(participants)} が参加しています"
        await message.channel.send(text)

    elif message.content.upper().startswith('/LEAVE'):
        for mention in message.mentions:
            participants.remove(mention.name)
            survivors.remove(mention.name)
        text = f"{' '.join(participants)} が参加しています"
        await message.channel.send(text)

    elif message.content.upper().startswith('/CREATE'):
        for mention in message.mentions:
            new_channel = await create_self_channel(message.guild, mention.id)
            text = f'{new_channel.mention} を作成しました'
            await message.channel.send(text)

    if message.content.upper() == '/MUTE':
        for voice_channel in message.guild.voice_channels:
            for member in voice_channel.members:
                await member.edit(mute=True)

    if message.content.upper() == '/UNMUTE':
        for voice_channel in message.guild.voice_channels:
            for member in voice_channel.members:
                await member.edit(mute=False)

    if message.content.upper().startswith('/MOVE'):
        given_name = message.content.split(' ')[-1]
        for channel in message.guild.channels:
            if channel.name == given_name:
                for mention in message.mentions:
                    await mention.move_to(channel)

    elif message.content.upper() == '/START':
        log_channel = await get_channel(message.guild, 'log')
        times_channel = await get_channel(message.guild, 'times')
        scheduler = Scheduler(log_channel, times_channel, participants)
        await asyncio.sleep(10)
        bot.loop.create_task(scheduler.start())


@bot.command()
async def get_channel(guild, given_name):
    for channel in guild.channels:
        if channel.name == given_name:
            return channel


# @bot.event
# async def create_text_channel(message, channel_name):
#     category_id = message.channel.category_id
#     category = message.guild.get_channel(category_id)
#     new_channel = await category.create_text_channel(name=channel_name)
#     return new_channel

@bot.event
async def create_log_channel(guild, name):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(send_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    new_channel = await guild.create_text_channel(name, overwrites=overwrites)
    return new_channel

@bot.event
async def create_self_channel(guild, user_id):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.get_member(user_id): discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    new_channel = await guild.create_text_channel(bot.get_user(user_id).display_name, overwrites=overwrites)
    return new_channel

@bot.event
async def create_voice_channel(guild, name):
    new_channel = await guild.create_voice_channel(name)
    return new_channel


bot.run(TOKEN)