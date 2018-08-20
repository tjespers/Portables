import discord
from discord.ext import commands
import os
from sys import exit
from subprocess import call
import sys
sys.path.append('../')
from main import config_load
from main import prefix
from datetime import datetime, timedelta, timezone
import re
from main import isLogging
from main import toggleLogging
import psutil
from main import addCommand
from main import getCommandsAnswered
from cogs.logs import getEventsLogged
from main import timeDiffToString

initialCpuUsage = psutil.cpu_percent(interval=None)

config = config_load()

def restart():
    print("Restarting script...")
    '''
    dir = os.path.dirname(os.path.realpath(__file__))
    parentDir = os.path.abspath(os.path.join(dir, os.pardir))
    cmdline = "Portables.bat"
    call("start cmd /K " + cmdline, cwd=parentDir, shell=True)
    print("New script started, quitting...")
    '''
    exit(0)

def pingToString(time):
    seconds = time.seconds
    microseconds = time.microseconds
    ms = seconds*1000 + int(microseconds/1000)
    time = str(ms) + ' ms'
    return time

class Management:
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.utcnow()
        server = bot.get_server(config['portablesServer'])
        self.server = server

    @commands.command(pass_context=True)
    async def status(self, ctx):
        '''
        Returns the bot's current status.
        '''
        now = datetime.utcnow()
        await self.bot.send_typing(ctx.message.channel)
        addCommand()
        time = now.replace(microsecond=0)
        time -= self.start_time
        time = timeDiffToString(time)
        msg_time = ctx.message.timestamp
        dif = 0
        if now > msg_time:
            dif = now - msg_time
        else:
            dif = msg_time - now
        ping = pingToString(dif)
        cpuPercent = str(psutil.cpu_percent(interval=None))
        cpuFreq = psutil.cpu_freq()[0]
        ram = psutil.virtual_memory() # total, available, percent, used, free, active, inactive, buffers, cached, shared, slab
        ramPercent = ram[2]
        ramTotal = ram[0]
        ramUsed = ram[3]
        title = f'**Status**'
        colour = 0x00e400
        timestamp = datetime.utcnow()
        txt = f'**OK**. :white_check_mark: \n'
        embed = discord.Embed(title=title, colour=colour, timestamp=timestamp, description=txt)
        embed.add_field(name='CPU', value=f'{cpuPercent}% {int(cpuFreq)} MHz', inline=False)
        embed.add_field(name='RAM', value=f'{ramPercent}% {int(ramUsed/1000000)}/{int(ramTotal/1000000)} MB', inline=False)
        embed.add_field(name='Ping', value=f'{ping}', inline=False)
        embed.add_field(name='Running time', value=f'{time}', inline=False)
        embed.add_field(name='Commands', value=f'{getCommandsAnswered()} commands answered', inline=False)
        embed.add_field(name='Events', value=f'{getEventsLogged()} events logged', inline=False)
        await self.bot.send_message(ctx.message.channel, embed=embed)
        return

    @commands.command(pass_context=True)
    async def restart(self, ctx):
        '''
        Restarts the bot (Leader+).
        '''
        addCommand()
        user = ctx.message.author
        roles = user.roles
        isLeader = False
        for r in roles:
            if r.id == config['leaderRole'] or user.id == config['owner']:
                isLeader = True
                break
        if not isLeader:
            await self.bot.say('Sorry, only leaders have permission to do this.')
            return
        else:
            await self.bot.say('OK, restarting...')
            restart()

    @commands.command(pass_context=True)
    async def say(self, ctx):
        '''
        Makes the bot say something (Leader+).
        '''
        addCommand()
        user = ctx.message.author
        roles = user.roles
        isLeader = False
        for r in roles:
            if r.id == config['leaderRole'] or user.id == config['owner']:
                isLeader = True
                break
        if not isLeader:
            await self.bot.say('Sorry, only leaders have permission to do this.')
            return
        msg = ctx.message
        if not msg.channel_mentions:
            serverChannel = msg.server.default_channel
            await self.bot.say(f'Please mention a channel for me to send the message to, such as: **-say {serverChannel.mention} test**')
            return
        channel = msg.channel_mentions[0]
        txt = msg.content
        txt = txt.replace("-say", "", 1)
        txt = txt.replace(channel.mention, "", 1)
        txt = txt.strip()
        if not txt:
            await self.bot.say(f'Please add text to your command, such as: **-say {channel.mention} test**')
            return
        try:
            await self.bot.send_message(channel, txt)
            await self.bot.delete_message(msg)
        except discord.Forbidden:
            await self.bot.say(f'Sorry, I do not have permission to send a message to {channel.mention}.')
        return

    @commands.command(pass_context=True)
    async def log(self, ctx):
        '''
        Toggles logging (Leader+).
        '''
        addCommand()
        isLeader = False
        for r in ctx.message.author.roles:
            if r.id == config['leaderRole'] or ctx.message.author.id == config['owner']:
                isLeader = True
                break
        if not isLeader:
            await self.bot.say('Sorry, only leaders have permission to do this.')
            return
        logging = isLogging()
        toggleLogging()
        if logging:
            await self.bot.say(f'Logging has been **disabled**.')
        else:
            await self.bot.say(f'Logging has been **enabled**.')
        return


def setup(bot):
    bot.add_cog(Management(bot))
