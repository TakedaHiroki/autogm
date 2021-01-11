import time
import asyncio

class Scheduler():
    def __init__(self, logs_channel, times_channel, participants):
        self.logs_channel = logs_channel
        self.times_channel = times_channel

    async def start(self):
        while True:
            if await self.nighttime():
                break
            if await self.daytime():
                break
            if await self.votetime():
                break
            
    async def daytime(self):
        await self.times_channel.send('昼時間です')
        t_start = time.time()
        while time.time() - t_start < 60:
            await self.times_channel.send(str(int(time.time() - t_start)))
            await asyncio.sleep(10)
        else:
            return False
        return True

    async def nighttime(self):
        await self.times_channel.send('夜時間です')
        t_start = time.time()
        while time.time() - t_start < 30:
            await self.times_channel.send(str(int(time.time() - t_start)))
            await asyncio.sleep(10)
        else:
            return False
        return True

    async def votetime(self):
        await self.times_channel.send('投票時間です')
        t_start = time.time()
        while time.time() - t_start < 30:
            await self.times_channel.send(str(int(time.time() - t_start)))
            await asyncio.sleep(10)
        else:
            return False
        return True

