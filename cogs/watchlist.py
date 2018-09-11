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
import validators

pattern = re.compile('[\W_]+')

config = config_load()

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('data/gspread.json', scope)
client = gspread.authorize(creds)

sheet = client.open(config['sheetName']).get_worksheet(4)

headerRows = 5

def regen():
    global creds
    global client
    global sheet
    creds = ServiceAccountCredentials.from_json_keyfile_name('data/gspread.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open(config['sheetName']).get_worksheet(4)

class watchlist:
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
    async def watchlist(self, ctx, name="", *reasons):
        '''
        Adds a player to the watchlist (Rank+).
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
        if not name:
            await self.bot.say('Please add the name of the player you want to add to the watchlist.')
            return
        name = re.sub('[^A-z0-9 -]', '', name).replace('`', '').strip()
        if len(name) > 12:
            await self.bot.say('Sorry, you can only add helpers with a valid RSN. RSNs have a maximum length of 12 characters.')
            return
        if re.match('^[A-z0-9 -]+$', name) is None:
            await self.bot.say('Sorry, you can only add helpers with valid a RSN. RSNs can only contain alphanumeric characters, spaces, and hyphens.')
            return
        if not reasons:
            await self.bot.say(f'Please provide your reason for adding **{name}** to the watchlist.')
            return
        screenshot = ''
        reasons = list(reasons)
        if validators.url(reasons[len(reasons)-1]):
            screenshot = reasons[len(reasons)-1]
            del reasons[len(reasons)-1]
        reason = ""
        for i, r in enumerate(reasons):
            reason += r
            if i < len(reasons) - 1:
                reason += ' '
        try:
            watchlist = sheet.col_values(1)[headerRows:]
        except:
            regen()
            watchlist = sheet.col_values(1)[headerRows:]
        for i, player in enumerate(watchlist):
            if not player:
                watchlist = watchlist[:i]
                break
        timestamp = datetime.utcnow().strftime("%b %#d, %Y")
        userName = user.nick
        if not userName:
            userName = user.name
        userName = re.sub('[^A-z0-9 -]', '', userName).replace('`', '').strip()
        count = 1
        for player in watchlist:
            if name.upper() == player.upper():
                count += 1
        row = headerRows + len(watchlist) + 1
        values = [name, timestamp, userName, reason, screenshot]
        try:
            sheet.insert_row(values, row)
        except:
            regen()
            sheet.insert_row(values, row)
        await self.bot.say(f'**{name}** has been added to the watchlist ({str(count)}).')


def setup(bot):
    bot.add_cog(watchlist(bot))
