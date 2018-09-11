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

sheet = client.open(config['sheetName']).get_worksheet(5)

headerRows = 5

def regen():
    global creds
    global client
    global sheet
    creds = ServiceAccountCredentials.from_json_keyfile_name('data/gspread.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open(config['sheetName']).get_worksheet(5)

class banlist:
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
    async def addban(self, ctx, name="", *reasons):
        '''
        Adds a player to the banlist (Mod+).
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
        isMod = False
        for r in roles:
            if r.id == self.mod.id or user.id == config['owner']:
                isMod = True
                break
        if not isMod:
            await self.bot.say('Sorry, this command can only be used by Moderators.')
            return
        if not name:
            await self.bot.say('Please add the name of the player you want to add to the banlist.')
            return
        name = re.sub('[^A-z0-9 -]', '', name).replace('`', '').strip()
        if len(name) > 12:
            await self.bot.say('Sorry, you can only banlist players with a valid RSN. RSNs have a maximum length of 12 characters.')
            return
        if re.match('^[A-z0-9 -]+$', name) is None:
            await self.bot.say('Sorry, you can only banlist players with valid a RSN. RSNs can only contain alphanumeric characters, spaces, and hyphens.')
            return
        if not reasons:
            await self.bot.say(f'Please provide your reason for adding **{name}** to the banlist.')
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
            banlist = sheet.col_values(1)[headerRows:]
            durations = sheet.col_values(2)[headerRows:]
        except:
            regen()
            banlist = sheet.col_values(1)[headerRows:]
            durations = sheet.col_values(2)[headerRows:]
        permaBanIndex = durations.index('Permanent Bans') + 1
        tempBans = []
        permaBans = []
        exBans = []
        for i, player in enumerate(banlist):
            if not player:
                tempBans = banlist[:i]
                break
        for i, player in enumerate(banlist):
            if i < permaBanIndex:
                continue
            if not player:
                permaBans = banlist[permaBanIndex:i]
                exBans = banlist[i+1:]
                break
        for player in tempBans:
            if name.upper() == player.upper():
                await self.bot.say(f'**{name}** is already on the banlist.')
                return
        for player in permaBans:
            if name.upper() == player.upper():
                await self.bot.say(f'**{name}** is already on the banlist.')
                return
        row = headerRows + len(tempBans) + 1
        count = 1
        for player in exBans:
            if name.upper() == player.upper():
                count += 1
        timestamp = datetime.utcnow().strftime("%b %#d, %Y")
        endTime = (datetime.utcnow() + relativedelta(days=+14)).strftime("%b %#d, %Y")
        userName = user.nick
        if not userName:
            userName = user.name
        userName = re.sub('[^A-z0-9 -]', '', userName).replace('`', '').strip()
        values = [name, '2 weeks', timestamp, endTime, reason, userName, 'Pending', '', screenshot]
        try:
            sheet.insert_row(values, row)
        except:
            regen()
            sheet.insert_row(values, row)
        await self.bot.say(f'**{name}** has been added to the banlist ({str(count)}).')
        await self.bot.send_message(self.adminChannel, f'**{name}** has been added to the banlist with status **Pending**.')


def setup(bot):
    bot.add_cog(banlist(bot))
