import asyncio
import random
import time
from collections import Counter

import discord
from discord.ext import commands


intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix='!',
    case_insensitive=True,
    intents=intents
)


TOKEN = ''

day = 1
user_info = {}
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
                await push_bite(message.author.name, dst)
                await message.channel.send(message.author.name+'さんは'+bite_results[message.author.name]+'さんを噛みました')
            else:
                await message.channel.send('もう一度やり直してください')

    elif message.content.startswith('護衛→'):
        if allocation[message.author.name] == '狩人':
            cmd, dst = message.content.split('→')
            if cmd == '護衛' and dst in survivors:
                await push_guard(message.author.name, dst)
                await message.channel.send(message.author.name+'さんは'+guard_results[message.author.name]+'さんを護衛しました')
            else:
                await message.channel.send('もう一度やり直してください')
            
    elif message.content.startswith('投票→'):
        cmd, dst = message.content.split('→')
        if cmd == '投票' and dst in survivors:
            await push_push(message.author.name, dst)
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
    global day
    await init_vote(survivors)
    await init_guard()
    await distribute_roles(roles)
    while True:
        await times_channel.send('夜時間です')
        if await count_rest_time(guild, log_channel, times_channel, 10):
            break
        day += 1
        await bite_process(guild, log_channel)
        if await check_game_end(log_channel):
            break
        for survivor in survivors:
            channel = await get_channel(guild, survivor.lower())
            await disable_channel_writing(guild, channel)
        await times_channel.send('昼時間です')
        if await count_rest_time(guild, log_channel, times_channel, 10):
            break
        if await vote_process(guild, log_channel, times_channel, 10):
            break
        if await check_game_end(log_channel):
            break
        
async def count_rest_time(guild, log_channel, times_channel, t):
    t_start = time.time()
    while time.time() - t_start < t:
        await times_channel.send(str(int(time.time() - t_start)))
        await asyncio.sleep(10)
    else:
        return False
    return True

async def bite_process(guild, log_channel):
    bite_result = list(bite_results.values())[0]
    for v in guard_results.values():
        if v == bite_result or allocation[bite_result] == '妖狐':
            text = '----------------------------------------------------------------\n■' + str(day) + '日目の朝になりました\n平和な朝を迎えました'
            await log_channel.send(text)
        else:
            text = '----------------------------------------------------------------\n■' + str(day) + '日目の朝になりました\n「' + bite_result + '」さんが無残な姿で発見されました'
            await log_channel.send(text)
            survivors.remove(bite_result)
            death.append(bite_result)
            print(bite_result)
            print(survivors)
            print(death)
            channel = await get_channel(guild, bite_result.lower())
            await disable_channel_writing(guild, channel)
    await init_bite()
    await init_guard()
    pass

async def vote_process(guild, log_channel, times_channel, t):
    for survivor in survivors:
        channel = await get_channel(guild, survivor.lower())
        await enable_channel_writing(guild, channel)
    await times_channel.send('投票時間です')
    if await count_rest_time(guild, log_channel, times_channel, t):
        return True
    most_voted_participant = [participant for participant, count in Counter(list(vote_results.values())).most_common() if count == Counter(list(vote_results.values())).most_common()[0][1]]
    text = '----------------------------------------------------------------\n■' + str(day) + '日目：1回目の投票結果\n'
    num_voted = Counter(list(vote_results.values()))
    for survivor in survivors:
        text += survivor + ' ' + str(num_voted[survivor]) + '票 投票先 → ' + vote_results[survivor] + '\n'
    await log_channel.send(text)
    if not len(most_voted_participant) == 1:
        await times_channel.send('再投票です')
        if await count_rest_time(guild, log_channel, times_channel, t):
            return True
        most_voted_participant = [participant for participant, count in Counter(list(vote_results.values())).most_common() if count == Counter(list(vote_results.values())).most_common()[0][1]]
        text = '----------------------------------------------------------------\n■' + str(day) + '日目：2回目の投票結果\n'
        num_voted = Counter(list(vote_results.values()))
        for survivor in survivors:
            text += survivor + ' ' + str(num_voted[survivor]) + '票 投票先 → ' + vote_results[survivor] + '\n'
        await log_channel.send(text)
        if not len(most_voted_participant) == 1:
            await times_channel.send('再投票です')
            if await count_rest_time(guild, log_channel, times_channel, t):
                return True
            most_voted_participant = [participant for participant, count in Counter(list(vote_results.values())).most_common() if count == Counter(list(vote_results.values())).most_common()[0][1]]
            text = '----------------------------------------------------------------\n■' + str(day) + '日目：3回目の投票結果\n'
            num_voted = Counter(list(vote_results.values()))
            for survivor in survivors:
                text += survivor + ' ' + str(num_voted[survivor]) + '票 投票先 → ' + vote_results[survivor] + '\n'
            await log_channel.send(text)
            if not len(most_voted_participant) == 1:
                await times_channel.send('再投票です')
                if await count_rest_time(guild, log_channel, times_channel, t):
                    return True
                most_voted_participant = [participant for participant, count in Counter(list(vote_results.values())).most_common() if count == Counter(list(vote_results.values())).most_common()[0][1]]
                text = '----------------------------------------------------------------\n■' + str(day) + '日目：4回目の投票結果\n'
                num_voted = Counter(list(vote_results.values()))
                for survivor in survivors:
                    text += survivor + ' ' + str(num_voted[survivor]) + '票 投票先 → ' + vote_results[survivor] + '\n'
                await log_channel.send(text)
                if not len(most_voted_participant) == 1:
                    text = '引き分けです'
                    await log_channel.send(text)
                    return True
    vote_result = most_voted_participant[0]
    survivors.remove(vote_result)
    death.append(vote_result)
    channel = await get_channel(guild, vote_result.lower())
    await disable_channel_writing(guild, channel)
    await init_vote(survivors)
    return False
    
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

async def check_game_end(log_channel):
    num_wolves = 0
    num_foxes = 0
    for survivor in survivors:
        if allocation[survivor] == 2:
            num_wolves += 1
        elif allocation[survivor] == 7:
            num_foxes += 1
    if num_wolves == 0:
        if num_foxes == 0:
            print(allocation)
            text = '「村 人」陣営の勝利です！！'
            await log_channel.send(text)
            return True
        else:
            print(allocation)
            text = '「妖 狐」陣営の勝利です！！'
            await log_channel.send(text)
            return True
    if len(survivors) - num_foxes <= num_wolves * 2:
        if num_foxes == 0:
            print(allocation)
            text = '「人 狼」陣営の勝利です！！'
            await log_channel.send(text)
            return True
        else:
            print(allocation)
            text = '「妖 狐」陣営の勝利です！！'
            await log_channel.send(text)
            return True
    return False

async def init_bite():
    bite_results.clear()

async def push_bite(src, dst):
    bite_results[src] = dst

async def init_guard():
    guard_results.clear()

async def push_guard(src, dst):
    guard_results[src] = dst

async def init_vote(survivors):
    vote_results.clear()
    for survivor in survivors:
        vote_results[survivor] = ''

async def push_push(src, dst):
    vote_results[src] = dst


bot.run(TOKEN)