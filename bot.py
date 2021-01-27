import os

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

DISCORD_BOT_TOKEN = os.environ['DISCORD_BOT_TOKEN']


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # set channels
    elif message.content == '.ag i':
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
    elif message.content == '.ag s':
        settings.day = 1
        settings.survivors = settings.participants[:]
        settings.death = []
        settings.roles = []
        settings.allocation = {}
        settings.is_game_end = False
        log_channel = await get_channel(message.guild, 'log')
        times_channel = await get_channel(message.guild, 'times')
        bot.loop.create_task(start_game(message.guild, log_channel, times_channel, settings.roles))

    # end game
    elif message.content == '.ag e':
        if not settings.is_game_end:
            text = '----------------------------------------------------------------\n'
            log_channel = await get_channel(message.guild, 'log')
            for survivor in settings.survivors:
                text += ('「' + str(survivor) +'」さんは無残な姿で発見されました\n')
            text += 'この村は廃村になりました……。'
            await log_channel.send(text)
            settings.is_game_end = True

    # join members with mention
    elif message.content.startswith('.ag j'):
        for mention in message.mentions:
            settings.participants.append(mention.name)
            settings.user_info[mention.name.lower()] = mention.id
        text = f"{' '.join(settings.participants)} が参加しています"
        await message.channel.send(text)

    # leave members with mention
    elif message.content.startswith('.ag l'):
        for mention in message.mentions:
            settings.participants.remove(mention.name)
            settings.survivors.remove(mention.name)
            del settings.user_info[mention.name.lower()]
        text = f"{' '.join(settings.participants)} が参加しています"
        await message.channel.send(text)

    # create channels for members
    elif message.content.startswith('ag c'):
        for mention in message.mentions:
            new_channel = await create_self_channel(message.guild, mention.id)
            text = f'{new_channel.mention} を作成しました'
            await message.channel.send(text)

    # mute voice channel
    if message.content == '.ag m':
        for voice_channel in message.guild.voice_channels:
            for member in voice_channel.members:
                await member.edit(mute=True)

    # unmute voice channel
    if message.content == '.ag um':
        for voice_channel in message.guild.voice_channels:
            for member in voice_channel.members:
                await member.edit(mute=False)

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


bot.run(DISCORD_BOT_TOKEN)