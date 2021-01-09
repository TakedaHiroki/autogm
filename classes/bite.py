class Bite():
    def __init__(self):
        self.src = ''
        self.dst = ''

    def push(self, src, dst):
        self.src = src
        self.dst = dst

    def clear(self):
        self.src = ''
        self.dst = ''