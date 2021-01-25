import time
import asyncio
from collections import Counter
import random

import settings


async def get_channel(guild, given_name):
    for channel in guild.channels:
        if channel.name == given_name:
            return channel

async def enable_channel_writing(guild, channel):
    member = guild.get_member(settings.user_info[channel.name])
    await channel.set_permissions(member, read_messages=True, send_messages=True)

async def disable_channel_writing(guild, channel):
    member = guild.get_member(settings.user_info[channel.name])
    await channel.set_permissions(member, read_messages=True, send_messages=False)

async def start_game(guild, log_channel, times_channel, roles):
    await settings.vote.reset(settings.survivors)
    await distribute_roles(roles)
    while True:
        await times_channel.send('夜時間です')
        if await count_rest_time(guild, log_channel, times_channel, 10):
            break
        settings.day += 1
        await bite_process(guild, log_channel)
        if await check_game_end(log_channel):
            break
        for survivor in settings.survivors:
            channel = await get_channel(guild, survivor.lower())
            await disable_channel_writing(guild, channel)
        await times_channel.send('昼時間です')
        if await count_rest_time(guild, log_channel, times_channel, 10):
            break
        if await vote_process(guild, log_channel, times_channel, 10):
            break
        if await check_game_end(log_channel):
            break

async def bite_process(guild, log_channel):
    bite_result = list(settings.bite.results.values())[0]
    for v in settings.guard.results.values():
        if v == bite_result or settings.allocation[bite_result] == '妖狐':
            text = '----------------------------------------------------------------\n■' + str(settings.day) + '日目の朝になりました\n平和な朝を迎えました'
            await log_channel.send(text)
        else:
            text = '----------------------------------------------------------------\n■' + str(settings.day) + '日目の朝になりました\n「' + bite_result + '」さんが無残な姿で発見されました'
            await log_channel.send(text)
            settings.survivors.remove(bite_result)
            variable.death.append(bite_result)
            channel = await get_channel(guild, bite_result.lower())
            await disable_channel_writing(guild, channel)
    await settings.bite.reset()
    await settings.guard.reset()
    pass

async def vote_process(guild, log_channel, times_channel, t):
    for survivor in settings.survivors:
        channel = await get_channel(guild, survivor.lower())
        await enable_channel_writing(guild, channel)
    await times_channel.send('投票時間です')
    if await count_rest_time(guild, log_channel, times_channel, t):
        return True
    most_voted_participant = [participant for participant, count in Counter(list(settings.vote.results.values())).most_common() if count == Counter(list(settings.vote.results.values())).most_common()[0][1]]
    text = '----------------------------------------------------------------\n■' + str(settings.day) + '日目：1回目の投票結果\n'
    num_voted = Counter(list(settings.vote.results.values()))
    for survivor in settings.survivors:
        text += survivor + ' ' + str(num_voted[survivor]) + '票 投票先 → ' + settings.vote.results[survivor] + '\n'
    await log_channel.send(text)
    if not len(most_voted_participant) == 1:
        await times_channel.send('再投票です')
        if await count_rest_time(guild, log_channel, times_channel, t):
            return True
        most_voted_participant = [participant for participant, count in Counter(list(settings.vote.results.values())).most_common() if count == Counter(list(settings.vote.results.values())).most_common()[0][1]]
        text = '----------------------------------------------------------------\n■' + str(settings.day) + '日目：2回目の投票結果\n'
        num_voted = Counter(list(settings.vote.results.values()))
        for survivor in settings.survivors:
            text += survivor + ' ' + str(num_voted[survivor]) + '票 投票先 → ' + settings.vote.results[survivor] + '\n'
        await log_channel.send(text)
        if not len(most_voted_participant) == 1:
            await times_channel.send('再投票です')
            if await count_rest_time(guild, log_channel, times_channel, t):
                return True
            most_voted_participant = [participant for participant, count in Counter(list(settings.vote.results.values())).most_common() if count == Counter(list(settings.vote.results.values())).most_common()[0][1]]
            text = '----------------------------------------------------------------\n■' + str(settings.day) + '日目：3回目の投票結果\n'
            num_voted = Counter(list(settings.vote.results.values()))
            for survivor in settings.survivors:
                text += survivor + ' ' + str(num_voted[survivor]) + '票 投票先 → ' + settings.vote.results[survivor] + '\n'
            await log_channel.send(text)
            if not len(most_voted_participant) == 1:
                await times_channel.send('再投票です')
                if await count_rest_time(guild, log_channel, times_channel, t):
                    return True
                most_voted_participant = [participant for participant, count in Counter(list(settings.vote.results.values())).most_common() if count == Counter(list(settings.vote.results.values())).most_common()[0][1]]
                text = '----------------------------------------------------------------\n■' + str(settings.day) + '日目：4回目の投票結果\n'
                num_voted = Counter(list(settings.vote.results.values()))
                for survivor in settings.survivors:
                    text += survivor + ' ' + str(num_voted[survivor]) + '票 投票先 → ' + settings.vote.results[survivor] + '\n'
                await log_channel.send(text)
                if not len(most_voted_participant) == 1:
                    text = '引き分けです'
                    await log_channel.send(text)
                    return True
    vote_result = most_voted_participant[0]
    settings.survivors.remove(vote_result)
    variable.death.append(vote_result)
    channel = await get_channel(guild, vote_result.lower())
    await disable_channel_writing(guild, channel)
    await settings.guard.reset(settings.survivors)
    return False

async def decide_missing_role(roles):
    roles += settings.cast['村人'] * [1]
    roles += settings.cast['占い師'] * [3]
    roles += settings.cast['霊能者'] * [4]
    roles += settings.cast['狩人'] * [5]
    roles += settings.cast['狂人'] * [6]
    random.shuffle(settings.roles)
    missing_role = settings.roles.pop(0)
    return missing_role
    
async def distribute_roles(roles):
    missing_role = await decide_missing_role(settings.roles)
    settings.roles += settings.cast['人狼'] * [2]
    settings.roles += settings.cast['妖狐'] * [7]
    random.shuffle(settings.participants)
    random.shuffle(settings.roles)
    for idx in range(len(settings.participants)):
        settings.allocation[settings.participants[idx]] = settings.roles[idx]

async def check_game_end(log_channel):
    num_wolves = 0
    num_foxes = 0
    for survivor in settings.survivors:
        if settings.allocation[survivor] == 2:
            num_wolves += 1
        elif settings.allocation[survivor] == 7:
            num_foxes += 1
    if num_wolves == 0:
        if num_foxes == 0:
            text = '「村 人」陣営の勝利です！！'
            await log_channel.send(text)
            return True
        else:
            text = '「妖 狐」陣営の勝利です！！'
            await log_channel.send(text)
            return True
    if len(settings.survivors) - num_foxes <= num_wolves * 2:
        if num_foxes == 0:
            text = '「人 狼」陣営の勝利です！！'
            await log_channel.send(text)
            return True
        else:
            text = '「妖 狐」陣営の勝利です！！'
            await log_channel.send(text)
            return True
    return False

async def count_rest_time(guild, log_channel, times_channel, t):
    t_start = time.time()
    while time.time() - t_start < t:
        await times_channel.send(str(int(time.time() - t_start)))
        await asyncio.sleep(10)
    else:
        return False
    return True