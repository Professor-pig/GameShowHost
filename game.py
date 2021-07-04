import discord
import player
import random


class Game:
    def __init__(self):
        self.status = str()
        self.original_players = list()
        self.players_list = list()
        self.round_n = int()
        self.creator = player.Player()
        self.next_turns = list()
        self.total_votes = int()
        self.voted_for = dict()
        self.channel = None
        self.winning = int()

    def __getitem__(self, item):
        return {
            "status": self.status,
            "initiated": self.status == "INITIATED",
            "playing": self.status == "PLAYING",
            "round": self.round_n,
            "players": self.players_list,
            "next player": self.next_turns[0] if self.next_turns else None,
            "next players": self.next_turns,
            "voting": self.status == "VOTING",
            "votes": self.total_votes,
            "channel": self.channel,
            "winning": self.winning,
            "original": self.original_players,
            "creator": self.creator
        }.get(item, None)

    def __setitem__(self, key, value):
        if key == "next players":
            self.next_turns = value
        elif key == "winning":
            self.winning = value

    async def add_player(self, user):
        this_player = player.Player(user)
        if not self.original_players:
            self.creator = this_player
        elif this_player in self.original_players:
            await this_player.send("{0}, you have already joined the game.".format(this_player))
            return
        else:
            await this_player.send("You have joined `{0}`'s game of *Who is the Spy?*".format(self.original_players[0]))
        self.original_players.append(this_player)

    def assign_words(self, word_combo):
        self.players_list = self.original_players.copy()
        num_spies = 1 if len(self.players_list) < 7 else 2
        current_spies = 0
        while current_spies < num_spies:
            spy = random.choice(self.players_list)
            if not spy["spy"]:
                spy["spy"] = True
                current_spies += 1
        if len(word_combo) == 2:
            spy_word = word_combo.pop(random.choice((0, 1)))
            normal_word = word_combo[0]
            for this_player in self.players_list:
                if this_player["spy"]:
                    this_player["word"] = spy_word
                else:
                    this_player["word"] = normal_word

    def clear(self):
        self.status = str()
        self.players_list = list()
        self.round_n = int()
        self.creator = player.Player()
        self.next_turns = list()
        self.total_votes = int()
        self.voted_for = dict()
        self.winning = int()

    def complete_turn(self):
        self.next_turns.pop(0)

    def end(self):
        self.channel = None
        self.original_players = list()

    def find_player(self, user: discord.abc.Messageable):
        for this_player in self.players_list:
            if this_player == user:
                return this_player

    async def initiate(self, creator, channel: discord.TextChannel):
        self.status = "INITIATED"
        await self.add_player(creator)
        self.round_n = 0
        self.channel = channel

    def kick(self):
        to_kick = None
        highest_votes = 0
        for this_player in self.players_list:
            votes = this_player["votes"]
            if votes == highest_votes:
                to_kick = None
            elif votes > highest_votes:
                to_kick = this_player
                highest_votes = votes
        if to_kick:
            self.players_list.remove(to_kick)
        return to_kick

    def new_round(self):
        self.status = "PLAYING"
        self.round_n += 1

    def is_playing(self, user):
        for this_player in self.players_list:
            if this_player == user:
                return True
        return False

    def role_count(self):
        spies, plebeians = 0, 0
        for this_player in self.players_list:
            if this_player["spy"]:
                spies += 1
            else:
                plebeians += 1
        return spies, plebeians

    async def start_voting(self, send_embed):
        description = "Time to vote. Here are the candidates:\n\n{0}\n\nType the number of who you vote for.".format(
            "\n".join("`{0}\t{1}`".format(i + 1, suspect) for i, suspect in enumerate(self.players_list))
        )
        for this_player in self.players_list:
            await send_embed(
                description,
                title="Vote",
                channel=this_player
            )
        self.status = "VOTING"
        self.total_votes = 0
        for this_player in self.players_list:
            this_player["votes"] = 0
        self.voted_for = {}

    def vote(self, candidate: player.Player, voter: discord.abc.Messageable) -> bool:
        candidate["votes"] += 1
        changing = str(voter) in self.voted_for
        self.voted_for[str(voter)] = candidate
        if changing:
            return True
        else:
            self.total_votes += 1
            return False
