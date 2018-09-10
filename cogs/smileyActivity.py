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

class smileyActivity:
    def __init__(self, bot):
        self.bot = bot
        server = bot.get_server(config['portablesServer'])
        roles = server.roles
        rank = discord.utils.get(roles, id=config['rankRole'])
        admin = discord.utils.get(roles, id=config['adminRole'])
        leader = discord.utils.get(roles, id=config['leaderRole'])
        adminChannel = bot.get_channel(config['adminChannel'])
        self.server = server
        self.rank = rank
        self.admin = admin
        self.leader = leader
        self.adminChannel = adminChannel

    @commands.command(pass_context=True)
    async def smileyactivity(self, ctx, *memberNames):
        '''
        Notes activity for a smiley on sheets (Rank+).
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

    @commands.command(pass_context=True)
    async def addsmiley(self, ctx, name=""):
        '''
        Adds a smiley to the sheets (Admin+).
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
                await self.bot.say('**{name}** is already on the list of smileys.')
                return
        row = 0
        for i, smiley in enumerate(smileys):
            if name.upper() == smiley.upper():
                row = i + headerRows + 1
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

    @commands.command(pass_context=True)
    async def activatesmiley(self, ctx, name=""):
        '''
        Sets smiley status to active (Leader+).
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
        for smiley in smileys:
            if name.upper() in smiley.upper():
                row = i + headerRows
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


def setup(bot):
    bot.add_cog(smileyActivity(bot))
