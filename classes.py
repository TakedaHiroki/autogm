class Bite:
    def __init__(self):
        self.results = {}

    async def reset(self):
        self.results.clear()

    async def push(self, src, dst):
        self.results[src] = dst


class Guard:
    def __init__(self):
        self.result = {}

    async def reset(self):
        self.results.clear()

    async def push(self, src, dst):
        self.results[src] = dst


class Vote:
    def __init__(self):
        self.results = {}

    async def reset(self, survivors):
        self.results.clear()
        for survivor in survivors:
            self.results[survivor] = ''

    async def push(self, src, dst):
        self.results[src] = dst