import discord
from discord.ext import commands
from main import config_load
from main import prefix
from datetime import datetime, timedelta, timezone
import sys
sys.path.append('../')
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
from main import addCommand
from main import timeDiffToString

config = config_load()

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('data/gspread.json', scope)
client = gspread.authorize(creds)

pattern = re.compile('([^\s\w]|_)+')

sheet = client.open(config['sheetName']).sheet1
locRow = sheet.row_values(21)
creditCell = str(sheet.cell(22, 5).value)
names = str(sheet.cell(22, 5).value)
timeCell = str(sheet.cell(22, 3).value)
abbrevCell = str(sheet.cell(22, 7).value)
notes = str(locRow[7])
title = '__Portables FC Locations__'
fletchers = str(locRow[0])
crafters = str(locRow[1])
braziers = str(locRow[2])
sawmills = str(locRow[3])
forges = str(locRow[4])
ranges = str(locRow[5])
wells = str(locRow[6])
colour = 0xff0000
now = datetime.utcnow()

description = (f'**Fletchers:**\t{fletchers}\n'
               f'**Crafters:**\t  {crafters}\n'
               f'**Braziers:**\t  {braziers}\n'
               f'**Sawmills:**\t {sawmills}\n'
               f'**Forges:**\t\t {forges}\n'
               f'**Ranges:**\t\t{ranges}\n'
               f'**Wells:**\t\t   {wells}')
description = description.replace('**', '~')
description = description.replace('*', '\\*')
description = description.replace('~', '**')

embed = discord.Embed(title=title, description=description, colour=colour)
embed.add_field(name='__Notes:__', value=notes, inline=False)
embed.add_field(name='__Abbreviations:__', value=abbrevCell, inline=False)

logo_url_lowres = 'https://i.gyazo.com/bf978e403612e295184a0d801d23fe87.png'
embed.set_thumbnail(url=logo_url_lowres)

name = names
name = name.split(',')[0]
name = name.split('&')[0]
name = name.split('/')[0]
name = name.split('|')[0]
name = name.strip()
name = pattern.sub('', name)
name = name.replace(' ', '%20')
player_image_url = f'https://services.runescape.com/m=avatar-rs/{name}/chat.png'
embed.set_author(name=names, url=discord.Embed.Empty, icon_url=player_image_url)

time = datetime.strptime(timeCell, '%d %b, %H:%M')
time = time.replace(year=now.year, second=now.second)
time = now - time
time = timeDiffToString(time)
if time:
    msg = 'Last updated ' + time + ' ago • ' + timeCell + '.'
else:
    msg = 'Updated just now • ' + timeCell + '.'
embed.set_footer(text=msg, icon_url=discord.Embed.Empty)

def regen():
    global creds
    global client
    global sheet
    creds = ServiceAccountCredentials.from_json_keyfile_name('data/gspread.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open(config['sheetName']).sheet1


class Portables:
    def __init__(self, bot):
        self.bot = bot
        self.botChannel = bot.get_channel(config['botChannel'])
        self.locChannel = bot.get_channel(config['locChannel'])
        self.start_time = datetime.utcnow()

    @commands.command(pass_context=True)
    async def regenPorts(self, ctx):
        '''
        A command to regenerate the OAuth2 key for the Google sheets API (Chatty only).
        '''
        addCommand()
        owner = config['owner']
        user = ctx.message.author
        if not user.id == owner:
            await self.bot.say('Sorry, only Chatty has permission to do this.')
            return
        try:
            regen()
            await self.bot.say('I have successfully regenerated my OAuth2 key.')
        except:
            await self.bot.say('Sorry, I failed to regenerate my OAuth2 key.')

    @commands.command(pass_context=True)
    async def portables(self, ctx):
        """
        A command to get the current portable locations.
        """
        addCommand()
        if ctx.message.channel != self.botChannel and ctx.message.channel != self.locChannel:
            await self.bot.say(f'Sorry, this command can only be used in the channel <#{self.botChannel.id}>.')
            return

        await self.bot.send_typing(ctx.message.channel)

        global embed
        global timeCell
        now = datetime.utcnow()

        try:
            timeCellNew = str(sheet.cell(22, 3).value)
        except:
            regen()
            timeCellNew = str(sheet.cell(22, 3).value)
        if timeCellNew == timeCell:
            time = datetime.strptime(timeCell, '%d %b, %H:%M')
            time = time.replace(year=now.year, second=now.second)
            time = now - time
            time = timeDiffToString(time)
            if time:
                msg = 'Last updated ' + time + ' ago • ' + timeCell + '.'
            else:
                msg = 'Updated just now • ' + timeCell + '.'
            embed.set_footer(text=msg, icon_url=discord.Embed.Empty)
            await self.bot.say(embed=embed)
            return
        else:
            timeCell = timeCellNew
            try:
                locRow = sheet.row_values(21)
                names = str(sheet.cell(22, 5).value)
            except:
                regen()
                locRow = sheet.row_values(21)
                names = str(sheet.cell(22, 5).value)
            fletchers = str(locRow[0])
            crafters = str(locRow[1])
            braziers = str(locRow[2])
            sawmills = str(locRow[3])
            forges = str(locRow[4])
            ranges = str(locRow[5])
            wells = str(locRow[6])
            description = (f'**Fletchers:**\t{fletchers}\n'
                           f'**Crafters:**\t  {crafters}\n'
                           f'**Braziers:**\t  {braziers}\n'
                           f'**Sawmills:**\t {sawmills}\n'
                           f'**Forges:**\t\t {forges}\n'
                           f'**Ranges:**\t\t{ranges}\n'
                           f'**Wells:**\t\t   {wells}')
            description = description.replace('**', '~')
            description = description.replace('*', '\\*')
            description = description.replace('~', '**')

            embed = discord.Embed(title=title, description=description, colour=colour)
            embed.add_field(name='__Notes:__', value=notes, inline=False)
            embed.add_field(name='__Abbreviations:__', value=abbrevCell, inline=False)

            name = names
            name = name.split(',')[0]
            name = name.split('&')[0]
            name = name.split('/')[0]
            name = name.split('|')[0]
            name = name.strip()
            name = pattern.sub('', name)
            name = name.replace(' ', '%20')
            player_image_url = f'https://services.runescape.com/m=avatar-rs/{name}/chat.png'
            embed.set_author(name=names, url=discord.Embed.Empty, icon_url=player_image_url)

            embed.set_thumbnail(url=logo_url_lowres)

            time = datetime.strptime(timeCell, '%d %b, %H:%M')
            time = time.replace(year=now.year, second=now.second)
            time = now - time
            time = timeDiffToString(time)
            if time:
                msg = 'Last updated ' + time + ' ago • ' + timeCell + '.'
            else:
                msg = 'Updated just now • ' + timeCell + '.'
            embed.set_footer(text=msg, icon_url=discord.Embed.Empty)
            await self.bot.say(embed=embed)
            return

def setup(bot):
    bot.add_cog(Portables(bot))
