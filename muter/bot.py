import discord
import re
from discord.ext import commands
from .config import Config
from .checks.messages import is_sent_by_bot


class Muter(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.id == bot.user.id:
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
        time = await self.check_time_arg(*args)
        if not time:
            await ctx.send('```Syntax: (digit)(unit; up to 8 hours; h, m, s)\nExample: 10m (10 minutes)'
                           + f'\nGiven Arguments: {" ".join(args)}```')
            return
        length = time[1]
        length = f'{length.get("h", 0)}h {length.get("m", 0)}m {length.get("s", 0)}s'
        await ctx.send(f'Muting {ctx.message.author.mention} for {length}...')
        return

    async def check_time_arg(self, *args):
        """Checks for time notation (hours, minutes, etc)"""
        mute_times = {}
        acceptable_units = ['h', 'm', 's']
        for time in args:
            digit = re.compile(r'([\d]+)([a-zA-Z]+)')
            try:
                digit_match = digit.match(time).groups()
            except AttributeError:
                return {}
            unit = digit_match[1]
            time = digit_match[0]
            if mute_times.get(unit) or unit not in acceptable_units:
                return {}
            mute_times[unit] = time
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
        print(total)
        if total > 28800:
            return False
        return total, duration


bot = commands.Bot(command_prefix='?', case_insensitive=True, description='Self Muter')
bot.add_cog(Muter(bot))


@bot.event
async def on_ready():
    print(f'Logged in as: {bot.user}.')


bot.run(Config.TOKEN)
