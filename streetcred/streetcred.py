import discord
from discord.ext import commands
from cogs.utils.dataIO import fileIO, dataIO
from cogs.utils.chat_formatting import box
from cogs.utils import checks
from __main__ import send_cmd_help
import logging
import os


log = logging.getLogger("red.streetcred")


class StreetCred:
    """Original code by Squid-Plugins, modded by Mak-and-Cheese"""

    def __init__(self, bot):
        self.bot = bot
        self.scores = fileIO("data/streetcred/scores.json", "load")
        self.settings = fileIO("data/streetcred/settings.json", 'load')
        for key in self.scores.keys():
            self._add_entry(key)

    def process_scores(self, member, is_downvote):
        member_id = member.id
        if not is_downvote:
            score_to_add = self.settings["CRED_YIELD"]
        else:
            score_to_add = -(self.settings["CRED_YIELD"])

        if member_id not in self.scores:
            self._add_entry(member_id)
        self.scores[member_id]["score"] += score_to_add
        fileIO("data/streetcred/scores.json", "save", self.scores)

    def _give_upvote(self, member, is_remove):
        member_id = member.id
        upvotes_given = self.scores[member_id]["upvotes_given"]
        if not is_remove:
            score_to_add = self.settings["UPVOTING_YIELD"]
        else:
            score_to_add = -(self.settings["UPVOTING_YIELD"])

        if member_id not in self.scores:
            self._add_entry(member_id)
        self.scores[member_id]["upvotes_given"] += score_to_add

        if upvotes_given % 1 == 0 and upvotes_given > 0:
            self.process_scores(member, False)
            self.scores[member_id]["upvotes_given"] = 0
        fileIO("data/streetcred/scores.json", "save", self.scores)

    def _process_upvote(self, member, upvote):
        member_id = member.id

        if member_id not in self.scores:
            self._add_entry(member_id)
        self.scores[member_id]["upvotes"] += upvote
        fileIO("data/streetcred/scores.json", "save", self.scores)

    def _process_downvote(self, member, downvote):
        member_id = member.id

        if member_id not in self.scores:
            self._add_entry(member_id)
        self.scores[member_id]["downvotes"] += downvote
        fileIO("data/streetcred/scores.json", "save", self.scores)

    def _add_entry(self, member):
        member_id = member

        if member_id in self.scores:
            if "score" not in self.scores.get(member_id, {}):
                self.scores[member_id]["score"] = 0
            if "upvotes" not in self.scores.get(member_id, {}):
                self.scores[member_id]["upvotes"] = 0
            if "downvotes" not in self.scores.get(member_id, {}):
                self.scores[member_id]["downvotes"] = 0
            if "upvotes_given" not in self.scores.get(member_id, {}):
                self.scores[member_id]["upvotes_given"] = 0
        else:
            self.scores[member_id] = {}
            self.scores[member_id]["score"] = 0
            self.scores[member_id]["upvotes"] = 0
            self.scores[member_id]["downvotes"] = 0
            self.scores[member_id]["upvotes_given"] = 0
        fileIO("data/streetcred/scores.json", "save", self.scores)

    def _add_reason(self, member_id, reason):
        if reason.lstrip() == "":
            return
        if member_id in self.scores:
            if "reasons" in self.scores.get(member_id, {}):
                old_reasons = self.scores[member_id].get("reasons", [])
                new_reasons = [reason] + old_reasons[:4]
                self.scores[member_id]["reasons"] = new_reasons
            else:
                self.scores[member_id]["reasons"] = [reason]
        else:
            self.scores[member_id] = {}
            self.scores[member_id]["reasons"] = [reason]

    def _fmt_reasons(self, reasons):
        if len(reasons) == 0:
            return None
        ret = "```Latest Reasons:\n"
        for num, reason in enumerate(reasons):
            ret += "\t" + str(num + 1) + ") " + str(reason) + "\n"
        return ret + "```"

    @commands.command(pass_context=True)
    async def streetcred(self, ctx):
        """Checks a user's streetcred, requires @ mention

           Example: !streetcred @Red"""
        if len(ctx.message.mentions) != 1:
            await send_cmd_help(ctx)
            return
        member = ctx.message.mentions[0]
        if self.scores.get(member.id, 0) != 0:
            member_dict = self.scores[member.id]
            await self.bot.say(member.name + " has " +
                               str(member_dict["score"]) + " points.")
            reasons = self._fmt_reasons(member_dict.get("reasons", []))
            if reasons:
                await self.bot.send_message(ctx.message.author, reasons)
        else:
            await self.bot.say(member.name + " has no street cred!")

    @commands.command(pass_context=True)
    async def upvotes(self, ctx):
        """Checks a user's upvote ratio, requires @ mention

           Example: !upvotes @Red"""
        if len(ctx.message.mentions) != 1:
            await send_cmd_help(ctx)
            return
        member = ctx.message.mentions[0]
        if self.scores.get(member.id, 0) != 0 or self.scores.get(member.id, 0) != 0:
            member_dict = self.scores[member.id]
            await self.bot.say(member.name + " has " +
                               str(member_dict["upvotes"]) + " upvotes and " +
                               str(member_dict["downvotes"]) + " downvotes.")
            reasons = self._fmt_reasons(member_dict.get("reasons", []))
            if reasons:
                await self.bot.send_message(ctx.message.author, reasons)
        else:
            await self.bot.say(member.name + " has no upvotes/downvotes.")

    @commands.command(pass_context=True)
    async def credlb(self, ctx, decending: bool=True):
        """Prints the streetcred leaderboard

        Example:
            leaderboard - displays scores top - bottom
            leaderboard False - displays scores bottom to top"""

        server = ctx.message.server
        member_ids = [m.id for m in server.members]

        karma_server_members = [key for key in self.scores.keys()
                                if key in member_ids]
        log.debug("Maki-Cogs server members:\n\t{}".format(
            karma_server_members))
        names = list(map(lambda mid: discord.utils.get(server.members, id=mid),
                         karma_server_members))
        log.debug("Names:\n\t{}".format(names))
        scores = list(map(lambda mid: self.scores[mid]["score"],
                          karma_server_members))
        log.debug("Scores:\n\t{}".format(scores))
        upvotes = list(map(lambda mid: self.scores[mid]["upvotes"],
                          karma_server_members))
        log.debug("Upvotes:\n\t{}".format(upvotes))
        downvotes = list(map(lambda mid: self.scores[mid]["downvotes"],
                          karma_server_members))
        log.debug("Downvotes:\n\t{}".format(downvotes))

        body = sorted(zip(names, scores, upvotes, downvotes), key=lambda tup: tup[1],
                      reverse=decending)[:10]
        karmaboard = ""
        place = 1
        for entry in body:
            karmaboard += str(place).rjust(2) + ". "
            karmaboard += str(entry[0]) + "\n"
            karmaboard += "\t\t" + "score: " + str(entry[1]).rjust(5) + " | "
            karmaboard += "+" + str(entry[2]).rjust(5) + " | "
            karmaboard += "-" + str(entry[3]).rjust(5) + "\n"
            place += 1

        if karmaboard != "":
            await self.bot.say(box(karmaboard, lang="py"))
        else:
            await self.bot.say("There are no entries.")

    @commands.group(pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def credset(self, ctx):
        """Manage streetcred settings"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @credset.command(name="upemote", pass_context=True, no_pm=True)
    async def _msgvote_upemoji(self, ctx, emoji):
        """Set the upvote emote"""

        emoji = str(self.fix_custom_emoji(ctx.message.server, emoji))
        self.settings["UP_EMOTE"] = emoji
        fileIO('data/streetcred/settings.json', 'save', self.settings)
        await self.bot.say("Upvote emoji set to: " + emoji)

    @credset.command(name="downemote", pass_context=True, no_pm=True)
    async def _msgvote_downemoji(self, ctx, emoji):
        """Set the downvote emote"""

        emoji = str(self.fix_custom_emoji(ctx.message.server, emoji))
        self.settings["DN_EMOTE"] = emoji
        fileIO('data/streetcred/settings.json', 'save', self.settings)
        await self.bot.say("Downvote emoji set to: " + emoji)

    @credset.command(pass_context=True, name="respond")
    async def _streetcredset_respond(self):
        """Toggles if bot will respond when points get added/removed"""
        if self.settings['RESPOND_ON_POINT']:
            await self.bot.say("Responses disabled.")
        else:
            await self.bot.say('Responses enabled.')
        self.settings['RESPOND_ON_POINT'] = \
            not self.settings['RESPOND_ON_POINT']
        fileIO('data/streetcred/settings.json', 'save', self.settings)

    @credset.command(pass_context=True, name="upyield")
    async def _streetcredset_yield(self, ctx, kpu: int):
        """Amount of streetcred per upvote

        Example: yield 1"""
        self.settings["CRED_YIELD"] = kpu
        await self.bot.say("streetcred is now set to {} per upvote.".format(kpu))
        fileIO('data/streetcred/settings.json', 'save', self.settings)

    @credset.command(pass_context=True, name="upbonus")
    async def _streetcredset_upvotebonus(self, ctx, kpu: float):
        """The bonus the user gets upon upvoting

        Example: upvotebonus 0.2"""

        self.settings["UPVOTING_YIELD"] = kpu
        await self.bot.say("Upvote bonus is now set to {} per upvote.".format(kpu))
        fileIO('data/streetcred/settings.json', 'save', self.settings)

    def fix_custom_emoji(self, server, emoji):
        if emoji[:2] != "<:":
            return emoji
        return [r for r in server.emojis if r.name == emoji.split(':')[1]][0]

    async def on_reaction_add(self, reaction, user):
        if user == self.bot.user:
            return
        if reaction.emoji == self.fix_custom_emoji(reaction.message.server, self.settings["UP_EMOTE"]):
            self.process_scores(reaction.message.author, False)
            self._process_upvote(reaction.message.author, 1)
            self._give_upvote(user, False)
        elif reaction.emoji == self.fix_custom_emoji(reaction.message.server, self.settings["DN_EMOTE"]):
            self.process_scores(reaction.message.author, True)
            self._process_downvote(reaction.message.author, 1)

    async def on_reaction_remove(self, reaction, user):
        if user == self.bot.user:
            return
        if reaction.emoji == self.fix_custom_emoji(reaction.message.server, self.settings["UP_EMOTE"]):
            self.process_scores(reaction.message.author, True)
            self._process_upvote(reaction.message.author, -1)
            self._give_upvote(user, True)
        elif reaction.emoji == self.fix_custom_emoji(reaction.message.server, self.settings["DN_EMOTE"]):
            self.process_scores(reaction.message.author, False)
            self._process_downvote(reaction.message.author, -1)


def check_folder():
    if not os.path.exists("data/streetcred"):
        print("Creating data/streetcred folder...")
        os.makedirs("data/streetcred")


def check_file():
    scores = {}
    settings = {"RESPOND_ON_POINT": True, "CRED_YIELD": 1, "UPVOTING_YIELD": 0.2, "UP_EMOTE": "\ud83d\udc4d", "DN_EMOTE": "\ud83d\udc4e"}

    f = "data/streetcred/scores.json"
    if not fileIO(f, "check"):
        print("Creating default streetcred's scores.json...")
        fileIO(f, "save", scores)

    f = "data/streetcred/settings.json"
    if not fileIO(f, "check"):
        print("Creating default streetcred's scores.json...")
        fileIO(f, "save", settings)


def setup(bot):
    check_folder()
    check_file()
    bot.add_cog(StreetCred(bot))

