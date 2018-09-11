import discord
from discord.ext import commands
from main import config_load
from main import prefix
import sys
sys.path.append('../')
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from main import addCommand
from datetime import datetime, timedelta, timezone
import copy
from dateutil.relativedelta import relativedelta
import re

pattern = re.compile('[\W_]+')

config = config_load()

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('data/gspread.json', scope)
client = gspread.authorize(creds)

sheet = client.open(config['sheetName']).get_worksheet(3)

headerRows = 3

def regen():
    global creds
    global client
    global sheet
    creds = ServiceAccountCredentials.from_json_keyfile_name('data/gspread.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open(config['sheetName']).get_worksheet(3)

class helpers:
    def __init__(self, bot):
        self.bot = bot
        server = bot.get_server(config['portablesServer'])
        roles = server.roles
        rank = discord.utils.get(roles, id=config['rankRole'])
        mod = discord.utils.get(roles, id=config['modRole'])
        admin = discord.utils.get(roles, id=config['adminRole'])
        leader = discord.utils.get(roles, id=config['leaderRole'])
        adminChannel = bot.get_channel(config['adminChannel'])
        self.server = server
        self.rank = rank
        self.mod = mod
        self.admin = admin
        self.leader = leader
        self.adminChannel = adminChannel

    @commands.command(pass_context=True)
    async def helper(self, ctx, *names):
        '''
        Adds a helper, or notes activity for an existing helper (Rank+).
        '''
        await self.bot.send_typing(ctx.message.channel)
        msg = ctx.message
        user = msg.author
        roles = user.roles
        channel = msg.channel
        server = msg.server
        if server != self.server:
            await self.bot.say('Sorry, this command can only be used in the Portables Discord server.')
            return
        isRank = False
        for r in roles:
            if r.id == self.rank.id or user.id == config['owner']:
                isRank = True
                break
        if not isRank:
            await self.bot.say('Sorry, this command can only be used by ranks.')
            return
        if not names:
            await self.bot.say('Please add the name(s) of the helper(s) for whom you want to note activity.')
            return
        try:
            helpers = sheet.col_values(1)[headerRows:]
        except:
            regen()
            helpers = sheet.col_values(1)[headerRows:]
        for i, helper in enumerate(helpers):
            if not helper:
                helpers = helpers[:i]
                break
        timestamp = datetime.utcnow().strftime("%b %#d, %Y")
        userName = user.nick
        if not userName:
            userName = user.name
        userName = pattern.sub('', userName)
        for name in names:
            if len(name) > 12:
                await self.bot.say('Sorry, you can only add helpers with a valid RSN. RSNs have a maximum length of 12 characters.')
                continue
            if re.match('^[A-z0-9 -]+$', name) is None:
                await self.bot.say('Sorry, you can only add helpers with valid a RSN. RSNs can only contain alphanumeric characters, spaces, and hyphens.')
                continue
            onList = False
            row = 0
            for i, helper in enumerate(helpers):
                if pattern.sub('', name.upper()) in pattern.sub('', helper.upper()):
                    name = helper
                    row = i + headerRows + 1
                    onList = True
            if not onList:
                row = headerRows + len(helpers) + 1
                values = [name, 'Helper', timestamp, userName]
                try:
                    sheet.insert_row(values, row)
                except:
                    regen()
                    sheet.insert_row(values, row)
                await self.bot.say(f'**{name}** has been added to the helper sheet.')
            elif onList:
                try:
                    activity = sheet.row_values(row)[2:8]
                except:
                    regen()
                    activity = sheet.row_values(row)[2:8]
                print(str(activity))
                for i in [5, 3, 1]:
                    if len(activity) - 1 >= i:
                        del activity[i]
                for i in [2,1,0]:
                    if len(activity) - 1 >= i:
                        if not activity[i]:
                            del activity[i]
                if timestamp in activity:
                    await self.bot.say(f'Sorry, **{name}** has already been noted as active today.')
                    continue
                if len(activity) >= 3:
                    await self.bot.say(f'Sorry, **{name}** already has a full row of activity.')
                    continue
                timeCol = 3 + len(activity) * 2
                creditCol = timeCol + 1
                try:
                    sheet.update_cell(row, timeCol, timestamp)
                    sheet.update_cell(row, creditCol, userName)
                except:
                    regen()
                    sheet.update_cell(row, col, timestamp)
                    sheet.update_cell(row, creditCol, userName)
                await self.bot.say(f'**{name}** has been noted as active for **{timestamp}**.')



def setup(bot):
    bot.add_cog(helpers(bot))
