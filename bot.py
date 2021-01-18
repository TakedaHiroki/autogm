import asyncio
import random
import time

import discord
from discord.ext import commands


intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix='!',
    case_insensitive=True,
    intents=intents
)


TOKEN = ''

# cast = {
#     "村人" : 5,
#     "人狼" : 2,
#     "占い師" : 1,
#     "霊能者" : 1,
#     "狩人" : 1,
#     "狂人" : 1,
#     "妖狐" : 1
# }

cast = {
    "村人" : 2,
    "人狼" : 1,
    "占い師" : 0,
    "霊能者" : 0,
    "狩人" : 0,
    "狂人" : 0,
    "妖狐" : 0
}


user_info = {}
# participants = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
# survivors = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
participants = []
survivors = []
death = []
roles = []
allocation = {}
bite_results = {}
guard_results = {}
vote_results = {}


@bot.event
async def on_ready():
    print('ログインしました')


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    elif message.content.startswith('噛み→'):
        allocation[message.author.name] = '人狼'
        if allocation[message.author.name] == '人狼':
            cmd, dst = message.content.split('→')
            if cmd == '噛み' and dst in survivors:
                await bite_push(message.author.name, dst)
                await message.channel.send(message.author.name+'さんは'+bite_results[message.author.name]+'さんを噛みました')
            else:
                await message.channel.send('もう一度やり直してください')

    elif message.content.startswith('護衛→'):
        if allocation[message.author.name] == '狩人':
            cmd, dst = message.content.split('→')
            if cmd == '護衛' and dst in survivors:
                await guard_push(message.author.name, dst)
                await message.channel.send(message.author.name+'さんは'+guard_results[message.author.name]+'さんを護衛しました')
            else:
                await message.channel.send('もう一度やり直してください')
            
    elif message.content.startswith('投票→'):
        cmd, dst = message.content.split('→')
        if cmd == '投票' and dst in survivors:
            await vote_push(message.author.name, dst)
            await message.channel.send('あなたは'+vote_results[message.author.name]+'さんに投票しました')
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
            user_info[mention.name.lower()] = mention.id
        text = f"{' '.join(participants)} が参加しています"
        await message.channel.send(text)

    elif message.content.upper().startswith('/LEAVE'):
        for mention in message.mentions:
            participants.remove(mention.name)
            survivors.remove(mention.name)
            del user_info[mention.name.lower()]
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
        bot.loop.create_task(start(message.guild, log_channel, times_channel, roles))


@bot.command()
async def get_channel(guild, given_name):
    for channel in guild.channels:
        if channel.name == given_name:
            return channel

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

async def enable_channel_writing(guild, channel):
    member = guild.get_member(user_info[channel.name])
    await channel.set_permissions(member, read_messages=True, send_messages=True)

async def disable_channel_writing(guild, channel):
    member = guild.get_member(user_info[channel.name])
    await channel.set_permissions(member, read_messages=True, send_messages=False)

@bot.event
async def create_voice_channel(guild, name):
    new_channel = await guild.create_voice_channel(name)
    return new_channel

async def start(guild, log_channel, times_channel, roles):
    await vote_init(survivors)
    await guard_init()
    await distribute_roles(roles)
    while True:
        if await nighttime(guild, times_channel):
            break
        if await daytime(guild, log_channel, times_channel):
            break
        if await votetime(guild, times_channel):
            break
        
async def daytime(guild, log_channel, times_channel):
    bite_result = list(bite_results.values())[0]
    for v in guard_results.values():
        if v == bite_result or allocation[bite_result] == '妖狐':
            text = '平和な朝を迎えました'
            await log_channel.send(text)
        else:
            text = '「' + bite_result + '」さんが無残な姿で発見されました'
            await log_channel.send(text)
            survivors.remove(bite_result)
            death.append(bite_result)
            channel = await get_channel(guild, bite_result.lower())
            disable_channel_writing(guild, channel)
    await bite_init()
    await guard_init()
    for survivor in survivors:
        channel = await get_channel(guild, survivor.lower())
        await disable_channel_writing(guild, channel)
    await times_channel.send('昼時間です')
    t_start = time.time()
    while time.time() - t_start < 10:
        await times_channel.send(str(int(time.time() - t_start)))
        await asyncio.sleep(10)
    else:
        return False
    return True

async def nighttime(guild, times_channel):
    await times_channel.send('夜時間です')
    t_start = time.time()
    while time.time() - t_start < 10:
        await times_channel.send(str(int(time.time() - t_start)))
        await asyncio.sleep(10)
    else:
        return False
    return True

async def votetime(guild, times_channel):
    for survivor in survivors:
        channel = await get_channel(guild, survivor.lower())
        await enable_channel_writing(guild, channel)
    await times_channel.send('投票時間です')
    t_start = time.time()
    while time.time() - t_start < 10:
        await times_channel.send(str(int(time.time() - t_start)))
        await asyncio.sleep(10)
    else:
        return False
    return True

async def decide_missing_role(roles):
    roles += cast['村人'] * [1]
    roles += cast['占い師'] * [3]
    roles += cast['霊能者'] * [4]
    roles += cast['狩人'] * [5]
    roles += cast['狂人'] * [6]
    random.shuffle(roles)
    missing_role = roles.pop(0)
    return missing_role
    

async def distribute_roles(roles):
    missing_role = await decide_missing_role(roles)
    print(missing_role)
    roles += cast['人狼'] * [2]
    roles += cast['妖狐'] * [7]
    random.shuffle(participants)
    random.shuffle(roles)
    for idx in range(len(participants)):
        allocation[participants[idx]] = roles[idx]

async def bite_init():
    bite_results.clear()

async def bite_push(src, dst):
    bite_results[src] = dst

async def guard_init():
    guard_results.clear()

async def guard_push(src, dst):
    guard_results[src] = dst

async def vote_init(survivors):
    vote_results.clear()
    for survivor in survivors:
        vote_results[survivor] = ''

async def vote_push(src, dst):
    vote_results[src] = dst

bot.run(TOKEN)