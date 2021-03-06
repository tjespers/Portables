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

sheet = client.open(config['sheetName']).get_worksheet(2)

headerRows = 4

def regen():
    global creds
    global client
    global sheet
    creds = ServiceAccountCredentials.from_json_keyfile_name('data/gspread.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open(config['sheetName']).get_worksheet(2)

def isName(memberName, member):
    name = member.nick
    if not name:
        name = member.name
    name = name.upper()
    if memberName in pattern.sub('', name):
        return True
    else:
        return False

class smileyActivity:
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

    @commands.command(pass_context=True, aliases=['smiley', 'smileyactive', 'smileyact'])
    async def smileyactivity(self, ctx, *memberNames):
        '''
        Notes activity for a smiley on sheets (Rank+).
        Arguments: name, name_2 (optional), etc...
        Surround names containing spaces with quotation marks, e.g.: "name with spaces".
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
        if not memberNames:
            await self.bot.say('Please add the smiley(s) for whom you want to note activity on the sheets as argument(s).')
            return
        try:
            smileys = sheet.col_values(1)[headerRows:]
        except:
            regen()
            smileys = sheet.col_values(1)[headerRows:]
        for i, smiley in enumerate(smileys):
            if smiley is None or not smiley:
                smileys = smileys[:i]
                break
        timestamp = datetime.utcnow().strftime("%b %#d, %Y")
        userName = user.nick
        if not userName:
            userName = user.name
        userName = re.sub('[^A-z0-9 -]', '', userName).replace('`', '').strip()
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
            try:
                activity = sheet.row_values(row)
            except:
                regen()
                activity = sheet.row_values(row)
            status = activity[1]
            activity = activity[4:12]
            if 'alt' in status:
                await self.bot.say(f'**{name}** is an alt account, you do not need to track its activity.')
                continue
            for i in [7, 5, 3, 1]:
                if len(activity) - 1 >= i:
                    del activity[i]
            for i in [3,2,1,0]:
                if len(activity) - 1 >= i:
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

    @commands.command(pass_context=True, aliases=['addsmile'])
    async def addsmiley(self, ctx, name=""):
        '''
        Adds a smiley to the sheets (Admin+).
        Arguments: name.
        Surround names containing spaces with quotation marks, e.g.: "name with spaces".
        Constraints: name must be a valid RSN.
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
        isAdmin = False
        for r in roles:
            if r.id == self.admin.id or user.id == config['owner']:
                isAdmin = True
                break
        if not isAdmin:
            await self.bot.say('Sorry, this command can only be used by Admins.')
            return
        if not name:
            await self.bot.say('Please add the name of the player you want to add to the smileys sheet.')
            return
        if len(name) > 12:
            await self.bot.say('Sorry, you can only add smileys with a valid RSN. RSNs have a maximum length of 12 characters.')
            return
        if re.match('^[A-z0-9 -]+$', name) is None:
            await self.bot.say('Sorry, you can only add smileys with valid a RSN. RSNs can only contain alphanumeric characters, spaces, and hyphens.')
            return
        try:
            smileys = sheet.col_values(1)[headerRows:]
        except:
            regen()
            smileys = sheet.col_values(1)[headerRows:]
        currentSmileys = []
        for i, smiley in enumerate(smileys):
            if smiley is None or not smiley:
                currentSmileys = smileys[:i]
                break
        for smiley in currentSmileys:
            if name.upper() == smiley.upper():
                await self.bot.say(f'**{name}** is already on the list of smileys.')
                return
        row = 0
        for i, smiley in enumerate(smileys):
            if name.upper() == smiley.upper():
                row = i + headerRows + 1
                break
        if row:
            try:
                sheet.delete_row(row)
            except:
                regen()
                sheet.delete_row(row)
        row = headerRows + len(currentSmileys) + 1
        timestamp = datetime.utcnow().strftime("%b %#d, %Y")
        endTime = (datetime.utcnow() + relativedelta(months=+1)).strftime("%b %#d, %Y")
        values = [name, 'No', 'Applied', '', '', '', '', '', '', '', '', '', '', 'Pending', timestamp, endTime]
        try:
            sheet.insert_row(values, row)
        except:
            regen()
            sheet.insert_row(values, row)
        await self.bot.say(f'**{name}** has been added to the smileys sheet.')
        await self.bot.send_message(self.adminChannel, f'**{name}** has been added to the smileys sheet with status **Pending**.')

    @commands.command(pass_context=True, aliases=['activatesmile'])
    async def activatesmiley(self, ctx, name=""):
        '''
        Sets smiley status to active (Leader+).
        Arguments: name.
        Surround names containing spaces with quotation marks, e.g.: "name with spaces".
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
        isLeader = False
        for r in roles:
            if r.id == self.leader.id or user.id == config['owner']:
                isLeader = True
                break
        if not isLeader:
            await self.bot.say('Sorry, this command can only be used by Leaders.')
            return
        if not name:
            await self.bot.say('Please add the name of the player you want to add to the smileys sheet.')
            return
        try:
            smileys = sheet.col_values(1)[headerRows:]
        except:
            regen()
            smileys = sheet.col_values(1)[headerRows:]
        for i, smiley in enumerate(smileys):
            if smiley is None or not smiley:
                smileys = smileys[:i]
                break
        row = 0
        for i, smiley in enumerate(smileys):
            if name.upper() in smiley.upper():
                row = i + headerRows + 1
                name = smiley
                break
        if not row:
            await self.bot.say(f'Sorry, I could not find a smiley by the name **{name}**.')
            return
        col = 14
        try:
            status = sheet.cell(row, col).value
        except:
            regen()
            status = sheet.cell(row, col).value
        if status == 'Active':
            await self.bot.say(f'**{name}**\'s status was already set to active.')
            return
        try:
            sheet.update_cell(row, col, 'Active')
        except:
            regen()
            sheet.update_cell(row, col, 'Active')
        await self.bot.say(f'**{name}**\'s status has been set to active.')

    @commands.command(pass_context=True)
    async def addalt(self, ctx, name="", member=""):
        '''
        Adds a rank alt to the sheets (Admin+).
        Arguments: name, member.
        Member can be either a name or a mention.
        Surround names containing spaces with quotation marks, e.g.: "name with spaces".
        Constraints: name must be a valid RSN, member must be a rank.
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
        isAdmin = False
        for r in roles:
            if r.id == self.admin.id or user.id == config['owner']:
                isAdmin = True
                break
        if not isAdmin:
            await self.bot.say('Sorry, this command can only be used by Admins.')
            return
        if not name:
            await self.bot.say(f'Please add the name of the alt you want to add, e.g.: `{prefix[0]}addalt TestAlt @testUser`.')
            return
        if not member:
            await self.bot.say(f'Please add the name of the rank whose alt you want to add, or mention them, e.g.: `{prefix[0]}addalt TestAlt @testUser`.')
            return
        if msg.mentions:
            member = msg.mentions[0]
        else:
            memberName = pattern.sub('', member).upper()
            member = discord.utils.find(lambda m: isName(memberName, m) and m.top_role >= self.rank, server.members)
            if not member:
                await self.bot.say(f'Sorry, I could not find a rank by the name **{memberName}**.')
                return
        memberName = member.nick
        if not memberName:
            memberName = member.name
        memberName = re.sub('[^A-z0-9 -]', '', memberName).replace('`', '').strip()
        type = ''
        if member.top_role >= self.admin:
            type = 'Admin+ alt'
        elif member.top_role >= self.mod:
            type = 'Moderator alt'
        elif member.top_role >= self.rank:
            type = 'Rank alt'
        else:
            await self.bot.say(f'Sorry, I could not find the right rank for **{memberName}**, please check that this member is ranked.')
            return
        if len(name) > 12:
            await self.bot.say('Sorry, you can only add alts with a valid RSN. RSNs have a maximum length of 12 characters.')
            return
        if re.match('^[A-z0-9 -]+$', name) is None:
            await self.bot.say('Sorry, you can only add alts with a valid RSN. RSNs can only contain alphanumeric characters, spaces, and hyphens.')
            return
        try:
            smileys = sheet.col_values(1)[headerRows:]
            types = sheet.col_values(2)[headerRows:]
        except:
            regen()
            smileys = sheet.col_values(1)[headerRows:]
            types = sheet.col_values(2)[headerRows:]
        currentSmileys = []
        for i, smiley in enumerate(smileys):
            if not smiley:
                currentSmileys = smileys[:i]
                types = types[:i]
                break
        for smiley in currentSmileys:
            if name.upper() == smiley.upper():
                await self.bot.say(f'**{name}** is already on the list of smileys.')
                return
        row = 0
        if 'Rank' in type:
            for i, t in enumerate(types):
                if not 'ALT' in t.upper():
                    row = i + headerRows + 1
                    break
        elif 'Mod' in type:
            for i, t in enumerate(types):
                if not 'ADMIN' in t.upper() and not 'MODERATOR' in t.upper():
                    row = i + headerRows + 1
                    break
        elif 'Admin' in type:
            for i, t in enumerate(types):
                if not 'ADMIN' in t.upper():
                    row = i + headerRows + 1
                    break
        if not row:
            await self.bot.say(f'Sorry, I encountered an error.')
            return
        timestamp = datetime.utcnow().strftime("%b %#d, %Y")
        endTime = ''
        values = [name, type, f'{memberName} alt', '', '', '', '', '', '', '', '', '', '', 'Pending', timestamp, endTime]
        try:
            sheet.insert_row(values, row)
        except:
            regen()
            sheet.insert_row(values, row)
        await self.bot.say(f'**{memberName}**\'s alt, **{name}**, has been added to the smileys sheet.')
        await self.bot.send_message(self.adminChannel, f'**{memberName}**\'s alt, **{name}**, has been added to the smileys sheet with status **Pending**.')


def setup(bot):
    bot.add_cog(smileyActivity(bot))
