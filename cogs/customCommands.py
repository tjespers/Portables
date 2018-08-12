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
import html
import re
from main import addCommand
from main import timeDiffToString

config = config_load()

# Array for '-rank' command. Contains rolename and role id for every self-assignable role
ranks = [['WARBANDS', config['WARBANDS']],
         ['AMLODD', config['AMLODD']],
         ['HEFIN', config['HEFIN']],
         ['ITHELL', config['ITHELL']],
         ['TRAHAEARN', config['TRAHAEARN']],
         ['MEILYR', config['MEILYR']],
         ['CRWYS', config['CRWYS']],
         ['CADARN', config['CADARN']],
         ['IORWERTH', config['IORWERTH']],
         ['CACHE', config['CACHE']],
         ['SINKHOLE', config['SINKHOLE']],
         ['YEWS', config['YEWS']],
         ['GOEBIES', config['GOEBIES']],
         ['MERCHANT', config['MERCHANT']],
         ['HAPPYHOUR', config['HAPPYHOUR']]]

def pingToString(time):
    seconds = time.seconds
    microseconds = time.microseconds
    ms = seconds*1000 + int(microseconds/1000)
    time = str(ms) + 'ms'
    return time

class CustomCommands:
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.utcnow()
        server = bot.get_server(config['portablesServer'])
        self.server = server
        self.roleChannel = bot.get_channel(config['roleChannel'])

    @commands.command(pass_context=True)
    async def ping(self, ctx):
        '''
        Pings the bot to check latency.
        '''
        now = datetime.utcnow()
        addCommand()
        msg = ctx.message
        msg_time = msg.timestamp
        dif = 0
        if now > msg_time:
            dif = now - msg_time
        else:
            dif = msg_time - now
        time = pingToString(dif)
        await self.bot.say(f'Pong! `{time}`')
        return


    @commands.command(pass_context=True)
    async def ports(self, ctx):
        '''
        Explains how to get portable locations.
        '''
        addCommand()
        msg = ctx.message
        botChannel = config['botChannel']
        await self.bot.say(f'For a list of portable locations, please use the `{prefix[0]}portables` command in the <#{botChannel}> channel.')
        await self.bot.delete_message(msg)
        return

    @commands.command(pass_context=True)
    async def discord(self, ctx):
        '''
        Gives the link for the Portables discord server.
        '''
        addCommand()
        await self.bot.say(f'https://discord.me/portables')
        msg = ctx.message
        await self.bot.delete_message(msg)
        return

    @commands.command(pass_context=True)
    async def abbr(self, ctx):
        '''
        Explains all abbreviations.
        '''
        addCommand()
        message = ctx.message
        msg = (f'**Abbreviations:**\n\n'
               f'Portables:\n'
               f'• R = Ranges\n'
               f'• M = Mills (Sawmills)\n'
               f'• W = Wells\n'
               f'• FO = Forges\n'
               f'• C = Crafters\n'
               f'• B = Braziers\n'
               f'• FL = Fletchers\n\n'
               f'Locations:\n'
               f'• CA = Combat Academy\n'
               f'• BE = Beach\n'
               f'• BA = Barbarian Assault\n'
               f'• SP = Shantay Pass\n'
               f'• BU = Burthorpe\n'
               f'• CW = Castle Wars\n'
               f'• Prif = Prifddinas\n'
               f'• MG = Max Guild\n'
               f'• VIP = Menaphos VIP skilling area')
        await self.bot.say(msg)
        await self.bot.delete_message(message)
        return

    @commands.command(pass_context=True)
    async def sheets(self, ctx):
        '''
        Gives the link to the public Portables sheet.
        '''
        addCommand()
        txt='https://docs.google.com/spreadsheets/d/16Yp-eLHQtgY05q6WBYA2MDyvQPmZ4Yr3RHYiBCBj2Hc/pub'
        await self.bot.say(txt)
        msg = ctx.message
        await self.bot.delete_message(msg)
        return

    @commands.command(pass_context=True)
    async def forums(self, ctx):
        '''
        Gives the link to the Portables forum thread.
        '''
        addCommand()
        txt = 'http://services.runescape.com/m=forum/forums.ws?75,76,789,65988634'
        await self.bot.say(txt)
        msg = ctx.message
        await self.bot.delete_message(msg)
        return

    @commands.command(pass_context=True)
    async def twitter(self, ctx):
        '''
        Gives the link to the Portables twitter.
        '''
        addCommand()
        txt = 'https://www.twitter.com/PortablesRS'
        await self.bot.say(txt)
        msg = ctx.message
        await self.bot.delete_message(msg)
        return

    @commands.command(pass_context=True)
    async def invite(self, ctx):
        '''
        Gives an invite for the Portables Discord server.
        '''
        addCommand()
        txt = 'https://discord.gg/QhBCYYr'
        await self.bot.say(txt)
        msg = ctx.message
        await self.bot.delete_message(msg)
        return

    @commands.command(pass_context=True)
    async def dxp(self, ctx):
        '''
        Gives the Reddit link DXP info.
        '''
        addCommand()
        txt = 'https://redd.it/7zf7um'
        await self.bot.say(txt)
        msg = ctx.message
        await self.bot.delete_message(msg)
        return

    @commands.command(pass_context=True)
    async def rank(self, ctx, rank=""):
        '''
        Toggles the given rank.
        '''
        addCommand()
        if not rank:
            await self.bot.say(f'Please enter a valid rank, such as: `{prefix[0]}rank merchant`.\n'
                               f'For all available ranks, please check {self.roleChannel.mention}.')
            return
        validRank = False
        for r in ranks:
            if rank.upper() in r[0]:
                id = r[1]
                validRank = True
                break
        if not validRank:
            await self.bot.say(f'Sorry, I could not find the rank: **{rank}**.\n'
                               f'For all available ranks, please check {self.roleChannel.mention}.')
            return
        role = ""
        for r in self.server.roles:
            if r.id == id:
                role = r
                break
        if not role:
            chatty = discord.utils.get(self.server.members, id=config['owner'])
            await self.bot.say(f'Sorry, I could not find the corresponding role for rank: **{rank}**.\n'
                               f'Fix your shit {chatty.mention}.')
            return
        user = ctx.message.author
        hasRole = False
        for r in user.roles:
            if r == role:
                hasRole = True
                break
        if not hasRole:
            await self.bot.add_roles(user, role)
            await self.bot.say(f'{user.mention}, you joined **{role.name}**.')
        else:
            await self.bot.remove_roles(user, role)
            await self.bot.say(f'{user.mention}, you left **{role.name}**.')

    @commands.command(pass_context=True)
    async def git(self, ctx):
        '''
        Returns the link to the GitHub repository of this bot.
        '''
        addCommand()
        await self.bot.say('https://github.com/ChattyRS/Portables')

def setup(bot):
    bot.add_cog(CustomCommands(bot))
