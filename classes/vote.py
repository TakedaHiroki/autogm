class Vote():
    def __init__(self, survivors):
        self.result = {survivor : '' for survivor in survivors}

    def push(self, src, dst):
        self.result[src] = dst

    def clear(self):
        for survivor in self.result.keys():
            self.result[survivor] = ''