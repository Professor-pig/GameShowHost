import discord
import requests
import re
import random
from disconnectError import DisconnectError
import game


class GameShowHost:
    MAX_LENGTH = 20
    start_vote_message = "That's it! We're all done. Now it's time to vote who you think is the spy. Make sure to " \
                         "consider many different aspects, such as their facial expression when they talked about " \
                         "their word, the sound of their voice, and how they described it. Don't forget that some " \
                         "people could be using some devious strategies to conceal their identity! Always consider " \
                         "before making your decision, but don't take too long or others will kick you.\n "
    allow_pings = False

    def __init__(self):
        self.client = discord.Client(intents=discord.Intents.all())
        self.event = self.client.event

        # initialisation
        self.game = game.Game()
        self.me = None
        self.AT_me = str()

    async def new_round(self, game_number: int = 0, site: str = ""):
        self.game.new_round()
        if self.game["round"] == 1:
            for _ in range(20):
                random.shuffle(self.game["original"])
            word_combo = self.get_word_combo(game_number, site)
            self.game.assign_words(word_combo)
            order = "Here is the order:\n\n{0}\n\nLet us begin Round {1}!".format(
                "\n".join("`{}\t{}`".format(i + 1, this_player) for i, this_player in enumerate(self.game["players"])),
                self.game["round"]
            )
            for this_player in self.game["players"]:
                word = this_player["word"]
                await self.send_embed(
                    "Your word is ||`{0}`||\n{1}".format(
                        word + (" " * (self.MAX_LENGTH - len(word)) if self.MAX_LENGTH else ""),
                        order
                    ),
                    title="{0}Round 1{0}".format(" " * 20),
                    channel=this_player
                )
            self.game["winning"] = 2 if len(self.game["players"]) < 6 else 3
        else:
            title = "{1}Round {0}{1}".format(self.game["round"], " " * 20)
            order = "Here is the order:\n\n{0}\n\nLet us begin Round {1}!".format(
                "\n".join("`{}\t{}`".format(i + 1, this_player) for i, this_player in enumerate(self.game["players"])),
                self.game["round"]
            )
            for this_player in self.game["players"]:
                await self.send_embed(
                    order,
                    title=title,
                    channel=this_player
                )
        self.game["next players"] = self.game["players"].copy()

    @staticmethod
    def get_word_combo(game_number: int = 0, site: str = "") -> list:
        site = requests.get(site)
        all_combos = site.text.strip().split("\n")
        if game_number:
            combo = all_combos[game_number - 1]
        else:
            for _ in range(20):
                random.shuffle(all_combos)
            combo = random.choice(all_combos)
        return combo.split(",")

    @staticmethod
    def get_quote():
        response = requests.get("https://zenquotes.io/api/random")
        quote = re.findall("\"q\":\"([^\"]+)\"", response.text)[0]
        author = re.findall("\"a\":\"([^\"]+)\"", response.text)[0]
        return "{} - {}".format(quote, author)

    async def on_message(self, message):
        content, sender = message.content, message.author
        if sender == self.me:
            return
        channel, guild, lower = message.channel, message.guild, content.lower()

        # banish / summon
        if "goodbye" in lower:
            await channel.send("Goodbye!")
            await channel.send("`{0} has left the chat and will return when summoned.`".format(self.me))
            exit(0)
        if "come back" in lower:
            await channel.send("`{0} has been summoned and has returned to the chat.`".format(self.me))
            await channel.send("Hello, I was summoned back by ||{0}||.".format(message.author))
            return

        # PINGs
        if "ping me" in lower and self.allow_pings:
            await message.author.send("Hello {0}. You told me to PING you."
                                      .format(sender.mention))

        # actions
        if lower.startswith("say"):
            await channel.send(message.content[3:].strip().title() + "!")
        elif lower.startswith("inspire"):
            quote = self.get_quote()
            await channel.send(quote)

        # DM only
        if not guild:
            if content.isdigit():
                if not self.game["voting"]:
                    return
                if not self.game.is_playing(sender):
                    return
                number = int(content)
                if number < 1 or number > len(self.game["players"]):
                    await self.send_embed("That is not a valid vote. Please vote again.", title="Error", channel=sender)
                    return
                voted_player = self.game["players"][number - 1]
                if voted_player == sender:
                    await self.send_embed(
                        "Sorry, you can't vote for yourself (why would you though?)! Please vote again.",
                        title="Error",
                        channel=sender
                    )
                    return
                if self.game.vote(voted_player, sender):
                    await self.send_embed(
                        "You changed your vote to {0}.".format(voted_player["mention"]),
                        title="Changed Vote",
                        channel=sender
                    )
                else:
                    await self.send_embed(
                        "Thank you for voting in Round {0}. You voted for {1}. To change your vote type another number."
                        .format(self.game["round"], voted_player["mention"]),
                        title="You Voted",
                        channel=sender
                    )
                if self.game["votes"] == len(self.game["players"]):
                    kicked = self.game.kick()
                    if kicked:
                        await self.send_embed(
                            "GASP! You've been kicked from the game!",
                            title="KICKED!",
                            channel=kicked
                        )
                        spies, plebeians = self.game.role_count()
                        description = "{0} was voted out! ".format(kicked["mention"])
                        if spies == 0:
                            description += "Now there are no more spies left. Congratulations to the plebeians, you " \
                                           "have won the game!"
                            self.game.clear()
                        elif spies + plebeians == self.game["winning"]:
                            description += "Now there are only {0} players left. Congratulations to the spies, you " \
                                           "have won the game!".format(self.game["winning"])
                            self.game.clear()
                    else:
                        description = "The votes are in, and guess what happened? There was a tie!"
                    for this_player in self.game["original"]:
                        await self.send_embed(
                            description,
                            title="The Votes Are In!",
                            channel=this_player
                        )
                    if not self.game["status"]:
                        description = "Here are everybody's stats:\n" \
                                      "`                          PLAYER |   ROLE   | WORD                `\n"
                        for this_player in self.game["original"]:
                            description += "`{0}{1} | {2} | {3}`\n".format(
                                " " * (32 - len(this_player)),
                                this_player,
                                "   SPY  " if this_player["spy"] else "PLEBEIAN",
                                this_player["word"] + " " * (self.MAX_LENGTH -
                                                             len(this_player["word"]))
                            )
                        for this_player in self.game["original"]:
                            await self.send_embed(
                                description,
                                title="Stats",
                                channel=this_player,
                            )
                        self.game.end()
                    else:
                        await self.new_round()
            elif content.startswith("start game "):
                if self.game["initiated"]:
                    if self.game["creator"] != sender:
                        await self.send_embed(
                            "You cannot start a game which you did not create.",
                            title="Error",
                            channel=channel
                        )
                        return
                else:
                    await self.send_embed(
                        "No game has been created yet. To create a game, try `play a game`.",
                        title="Error",
                        channel=channel
                    )
                    return
                for user in self.game["channel"].guild.members:
                    if self.game["creator"] != user and not user.bot:
                        await self.game.add_player(user)
                if len(self.game["original"]) < 3:
                    await self.send_embed(
                        "You cannot play a game with less than 3 players.",
                        title="Error",
                        channel=channel
                    )
                    return
                matches = re.findall("^start game ([0-9]+) *(https*://.+)*?$", content)
                if matches:
                    matches = matches[0]
                    if matches:
                        game_number = 0
                        if len(matches) == 2:
                            game_number = int(matches[0])
                            if matches[1]:
                                site = matches[1]
                            else:
                                site = "https://raw.githubusercontent.com/Professor-pig/word-combos/main/words.txt"
                        elif len(matches) == 1:
                            game_number = int(matches[0])
                            site = "https://raw.githubusercontent.com/Professor-pig/word-combos/main/words.txt"
                        else:
                            return
                        await self.new_round(game_number, site)

            elif content == "all done":
                await self.game.start_voting(self.send_embed)
            return

        # guild only
        # PINGs
        if "ping everyone" in lower and self.allow_pings:
            times = sum(map(int, re.findall("ping everyone[a-z ]+([0-9]+) times*", lower)))
            if times == 0:
                times = 1
            for _ in range(times):
                for member in guild.members:
                    if member.bot:
                        continue
                    if member == message.author and "except me" not in lower:
                        await member.send("Hello {0}. You told me to PING everyone, so that includes you.\nIf you do "
                                          "not wish to be PINGed when you PING everyone, add \" except me\" at the end."
                                          .format(sender.mention))
                    elif member != self.me:
                        await channel.send(
                            "Hello {0}. I was told to PING you by {1}".format(member.mention, sender.mention)
                        )

        # games
        if lower == "debug":
            self.game = game.Game()
            await self.game.initiate(sender, channel)
            for member in guild.members:
                if (not member.bot) and (member != sender):
                    await self.game.add_player(member)
            await self.new_round()
            for member in guild.members:
                if not member.bot:
                    self.game.complete_turn()
            await channel.send(self.start_vote_message)
            await self.game.start_voting(self.send_embed)
        elif content == "{0} PLEASE STOP".format(self.AT_me):
            if sender == self.game["creator"]["user"]:
                self.game.clear()
                self.game.end()
            else:
                await channel.send("You cannot stop a game which you did not create.")
        elif "play a game" in lower and not self.game["status"]:
            self.game = game.Game()
            await self.game.initiate(sender, channel)
            await self.send_embed(
                "{0} has created a game of *Who is the Spy?*\nPlease now go your your DMs.".format(sender.mention),
                title="Game Created",
                channel=channel
            )
        # elif content == "\\join all".format(self.AT_me):
        #     if self.game["initiated"]:
        #         await self.game.add_player(sender)
        #     elif self.game["playing"]:
        #         await channel.send("Sorry, no more new members can join this game.")
        #     else:
        #         await channel.send("{0} No game has been created yet. To create a game, try `play a game`."
        #                            .format(sender.mention))
        # elif content == "{0} done".format(self.AT_me):
        #     if not self.game["playing"]:
        #         return
        #     if self.game["next player"] != sender:
        #         return
        #     await channel.send("Thank you for completing your turn, {0}.".format(sender))
        #     self.game.complete_turn()
        #     if len(self.game["next players"]) == 1:
        #         await channel.send("Finally, we have {0}. Please say something about your word."
        #                            .format(self.game["next player"]["mention"]))
        #     elif not self.game["next players"]:
        #         await channel.send(self.start_vote_message)
        #         await self.game.start_voting()
        #     else:
        #         await channel.send("Next up is {0}. Please say something about your word.".format(
        #             self.game["next player"]["mention"])
        #         )
        # elif "i vote for " in lower:
        #     await channel.send("Shh! Do not vote in the server. Only vote in your DM with this bot, otherwise the game "
        #                        "will be ruined and everybody will kick you.")

    async def on_connect(self):
        # initialisation
        self.me = self.client.user
        self.AT_me = self.me.mention
        print("Client {0} has connected.".format(str(self.me)[:-5]))

    async def on_ready(self):
        print("Client {0} is ready.".format(str(self.me)[:-5]))

    async def on_disconnect(self):
        raise DisconnectError("Client has disconnected.")

    def run(self, token_file: str = "TOKEN.txt"):
        with open(token_file) as TOKEN:
            self.client.run(TOKEN.read())

    @staticmethod
    async def send_embed(description="", **kwargs):
        embed = discord.Embed(
            title="**{0}**".format(kwargs["title"]) if kwargs.get("title", "") else "",
            description=description,
            colour=0xFF0000)
        message = await kwargs["channel"].send(embed=embed)
        for reaction in kwargs.get("reactions", ""):
            await message.add_reaction(reaction)
