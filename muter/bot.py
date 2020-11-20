import discord
import re
from discord.ext import commands, tasks
from .config import Config
import pymongo
from pymongo import MongoClient
import urllib
import datetime
import asyncio
# import time
from .checks.messages import is_sent_by_bot


class Muter(commands.Cog):
    def __init__(self, discord_bot: commands.Bot,
                 mongo_client: MongoClient,
                 mute_db,
                 mute_collection):
        self.client = mongo_client
        self.db = mute_db
        self.mutes = mute_collection
        self.bot = discord_bot
        self.guild = None
        self.prev_time = datetime.datetime.now().replace(microsecond=0)
        self.read_database.start()

    def cog_unload(self):
        self.read_database.cancel()
        self.mutes.delete_many({})

    @tasks.loop(seconds=1)
    async def read_database(self):
        channel = await self.bot.fetch_channel('777013090969583616')
        new_time = datetime.datetime.now().replace(microsecond=0)
        if new_time.second != self.prev_time.second:
            self.prev_time = new_time
            results = self.mutes.find({'end_time': str(new_time)})
            for user in results:
                guild = self.bot.get_guild(self.guild)
                member = guild.get_member(user_id=user['user_id'])
                role = discord.utils.get(member.guild.roles, name="Muted")
                await member.remove_roles(role)
                self.mutes.delete_one(user)
                await channel.send(f'Time limit reached! Unmuting <@!{user["user_id"]}>...')

    @read_database.before_loop
    async def before_read_database(self):
        print('waiting...')
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.id == self.bot.user.id:
            print('Not the Bot')

    @commands.command(name='prefix', brief='Changes the prefix of Self-Muter')
    async def _prefix(self, ctx: commands.Context, *, args):
        """Changes the prefix of the self-mute bot."""
        if len(args) > 1:
            await ctx.send('Invalid. Only 1 character can be set for prefixes.')
            return
        else:
            self.bot.command_prefix = args
            await ctx.send(f'```Command prefix set to: {args}```')
            return

    @commands.command(name='selfmute',
                      brief='Mutes yourself for the time limit set. Supports hours, minutes, and seconds.')
    async def _self_mute(self, ctx: commands.Context, *args):
        """Self mutes a user for the time limit they set.
        Parameters
        ----------
        ctx : commands.Context
            Context the command is being invoked under
            Includes various metadata of message
        args : str
            Takes in user-input. Will check for time notations (hours, minutes, etc.)
        """
        self.guild = ctx.guild.id
        time = await self.check_time_arg(*args)
        member = ctx.message.author
        if not time:
            await ctx.send('```Syntax: (digit)(unit; 5 secs to 8 hrs; h, m, s)\nExample: 10m (10 minutes)'
                           + f'\nGiven Arguments: {" ".join(args)}```')
            return
        end = await self.calculate_end_time(time[0])
        await self.add_user_to_db(ctx.message.author.id, end)
        length = time[1]
        length = f'{length.get("h", 0)}h {length.get("m", 0)}m {length.get("s", 0)}s'
        role = discord.utils.get(member.guild.roles, name="Muted")
        print(member)
        await member.add_roles(role)
        await ctx.send(f'Muting {ctx.message.author.mention} for {length}...')
        return

    async def check_time_arg(self, *args):
        """Checks for time notation (hours, minutes, etc)"""
        mute_times = {}
        acceptable_units = ['h', 'm', 's']
        for times in args:
            digit = re.compile(r'([\d]+)([a-zA-Z]+)')
            try:
                digit_match = digit.match(times).groups()
            except AttributeError:
                return {}
            unit = digit_match[1]
            times = digit_match[0]
            if mute_times.get(unit) or unit not in acceptable_units:
                return {}
            mute_times[unit] = times
        total = await self.validate_times(mute_times)
        if not total:
            return {}
        return total

    async def validate_times(self, duration: dict):
        """Validates given times
        PARAMETERS
        ----------
        duration : dict
            keys : 'hours', 'minutes', 'seconds'
        RETURNS
        --------
        total, duration : list
            total : total time in seconds
            duration : dictionary with respective units and lengths"""
        total = 0
        hours = int(duration.get('h', 0))
        minutes = int(duration.get('m', 0))
        seconds = int(duration.get('s', 0))
        total += (hours * 3600) + (minutes * 60) + seconds
        if total > 28800 or total < 5:
            return False
        return total, duration

    async def calculate_end_time(self, seconds):
        now = datetime.datetime.now().replace(microsecond=0)
        end = now + datetime.timedelta(seconds=seconds)
        return end

    async def add_user_to_db(self, user, end_time):
        end_time = end_time.replace(microsecond=0)
        user = {
            'user_id': user,
            'end_time': str(end_time)
        }
        mute = self.mutes.insert_one(user)


client = MongoClient(Config.MONGO_URL)
db = client.automuter
mutes = db.selfmuter

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='?', case_insensitive=True, description='Self Muter', intents=intents)
bot.add_cog(Muter(bot, client, db, mutes))


@bot.event
async def on_ready():
    print(f'Logged in as: {bot.user}.')
    loop = asyncio.get_event_loop()


bot.run(Config.TOKEN)
