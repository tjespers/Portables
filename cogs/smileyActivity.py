import discord
from discord.ext import commands
from main import config_load
from main import prefix
import sys
sys.path.append('../')
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
from main import addCommand
from datetime import datetime, timedelta, timezone
import copy

config = config_load()

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('data/gspread.json', scope)
client = gspread.authorize(creds)

sheet = client.open(config['sheetName']).get_worksheet(2)

pattern = re.compile('[\W_]+')

headerRows = 4

def isName(memberName, member):
    name = member.nick
    if not name:
        name = member.name
    name = name.upper()
    if memberName in pattern.sub('', name):
        return True
    else:
        return False

def regen():
    global creds
    global client
    global sheet
    creds = ServiceAccountCredentials.from_json_keyfile_name('data/gspread.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open(config['sheetName']).get_worksheet(2)

class smileyActivity:
    def __init__(self, bot):
        self.bot = bot
        server = bot.get_server(config['portablesServer'])
        roles = server.roles
        rank = discord.utils.get(roles, id=config['rankRole'])
        self.server = server
        self.rank = rank

    @commands.command(pass_context=True)
    async def smiley(self, ctx, *memberNames):
        '''
        Notes activity for a smiley on sheets (Rank+).
        '''
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
        if not memberNames:
            await self.bot.say('Please add the smiley(s) for whom you want to note activity on the sheets as argument(s).')
            return
        smileys = sheet.col_values(1)[headerRows:]
        for i, smiley in enumerate(smileys):
            if smiley is None or not smiley:
                smileys = smileys[:i]
                break
        timestamp = datetime.utcnow().strftime("%b %#d, %Y")
        userName = user.nick
        if not userName:
            userName = user.name
        for name in memberNames:
            row = 0
            for i, smiley in enumerate(smileys):
                if name.upper() in smiley.upper():
                    row = i + headerRows + 1
                    name = smiley
                    break
            if not row:
                await self.bot.say(f'Sorry, I could not find a smiley by the name **{name}**.')
                continue
            activity = sheet.row_values(row)
            status = activity[1]
            activity = activity[4:12]
            if 'alt' in status:
                await self.bot.say(f'**{name}** is an alt account, you do not need to track its activity.')
                continue
            for i in [7, 5, 3, 1]:
                del activity[i]
            for i in [3,2,1,0]:
                if activity[i] is None or not activity[i]:
                    del activity[i]
            if timestamp in activity:
                await self.bot.say(f'Sorry, **{name}** has already been noted as active today.')
                continue
            if len(activity) >= 4:
                await self.bot.say(f'Sorry, **{name}** already has a full row of activity.')
                continue
            timeCol = 5 + len(activity) * 2
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
    bot.add_cog(smileyActivity(bot))
