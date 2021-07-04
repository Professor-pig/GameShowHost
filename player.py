import discord


class Player:
    def __add__(self, other):
        return self.name + other

    def __eq__(self, other):
        return self.user == other

    def __init__(self, user: discord.Member = None):
        if user is None:
            self.user = None
            self.name = str()
            self.id = int()
        else:
            self.user = user
            self.name = str(user)[:-5]
            self.id = user.id
        self.word = str()
        self.spy = False
        self.votes = int()

    def __getitem__(self, item):
        if item == "word":
            return self.word
        elif item == "spy":
            return self.spy
        elif item == "user":
            return self.user
        elif item == "name":
            return self.name
        elif item == "id":
            return self.id
        elif item == "votes":
            return self.votes
        elif item == "mention":
            return self.user.mention

    def __len__(self):
        return len(self.name)

    def __ne__(self, other):
        return self.user != other

    def __repr__(self):
        return self.name

    def __setitem__(self, key, value):
        if key == "word":
            self.word = value
        elif key == "spy":
            self.spy = value
        elif key == "votes":
            self.votes = value

    def __str__(self):
        return self.name

    async def send(self, *args, **kwargs):
        return await self.user.send(*args, **kwargs)
