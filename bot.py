import discord
from discord.ext import commands

import settings
from internal import get_channel, start_game


intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix='!',
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
    
    # set channels
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

    # start game
    elif message.content.upper() == '/START':
        log_channel = await get_channel(message.guild, 'log')
        times_channel = await get_channel(message.guild, 'times')
        bot.loop.create_task(start_game(message.guild, log_channel, times_channel, settings.roles))

    # join members with mention
    elif message.content.upper().startswith('/JOIN'):
        for mention in message.mentions:
            settings.participants.append(mention.name)
            settings.survivors.append(mention.name)
            settings.user_info[mention.name.lower()] = mention.id
        text = f"{' '.join(settings.participants)} が参加しています"
        await message.channel.send(text)

    # leave members with mention
    elif message.content.upper().startswith('/LEAVE'):
        for mention in message.mentions:
            settings.participants.remove(mention.name)
            settings.survivors.remove(mention.name)
            del settings.user_info[mention.name.lower()]
        text = f"{' '.join(settings.participants)} が参加しています"
        await message.channel.send(text)

    # create channels for members
    elif message.content.upper().startswith('/CREATE'):
        for mention in message.mentions:
            new_channel = await create_self_channel(message.guild, mention.id)
            text = f'{new_channel.mention} を作成しました'
            await message.channel.send(text)

    # mute voice channel
    if message.content.upper() == '/MUTE':
        for voice_channel in message.guild.voice_channels:
            for member in voice_channel.members:
                await member.edit(mute=True)

    # unmute voice channel
    if message.content.upper() == '/UNMUTE':
        for voice_channel in message.guild.voice_channels:
            for member in voice_channel.members:
                await member.edit(mute=False)

    # move member to other voice channel
    if message.content.upper().startswith('/MOVE'):
        given_name = message.content.split(' ')[-1]
        for channel in message.guild.channels:
            if channel.name == given_name:
                for mention in message.mentions:
                    await mention.move_to(channel)

    # bite action
    elif message.content.startswith('噛み→'):
        settings.allocation[message.author.name] = '人狼'
        if settings.allocation[message.author.name] == '人狼':
            cmd, dst = message.content.split('→')
            if cmd == '噛み' and dst in settings.survivors:
                await settings.bite.push(message.author.name, dst)
                await message.channel.send(message.author.name+'さんは'+settings.bite.results[message.author.name]+'さんを噛みました')
            else:
                await message.channel.send('もう一度やり直してください')

    # guard action
    elif message.content.startswith('護衛→'):
        if settings.allocation[message.author.name] == '狩人':
            cmd, dst = message.content.split('→')
            if cmd == '護衛' and dst in settings.survivors:
                await settings.guard.push(message.author.name, dst)
                await message.channel.send(message.author.name+'さんは'+settings.guard.results[message.author.name]+'さんを護衛しました')
            else:
                await message.channel.send('もう一度やり直してください')

    # vote action
    elif message.content.startswith('投票→'):
        cmd, dst = message.content.split('→')
        if cmd == '投票' and dst in settings.survivors:
            await settings.vote.push(message.author.name, dst)
            await message.channel.send('あなたは'+settings.vote.results[message.author.name]+'さんに投票しました')
        else:
            await message.channel.send('もう一度やり直してください')

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