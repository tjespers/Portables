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

sheet = client.open(config['adminSheetName']).get_worksheet(1)

headerRows = 4

rankTitles = ['Sergeants', 'Corporals', 'Recruits', 'New']

def regen():
    global creds
    global client
    global sheet
    creds = ServiceAccountCredentials.from_json_keyfile_name('data/gspread.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open(config['adminSheetName']).get_worksheet(1)

class adminSheets:
    def __init__(self, bot):
        self.bot = bot
        server = bot.get_server(config['portablesServer'])
        roles = server.roles
        admin = discord.utils.get(roles, id=config['adminRole'])
        leader = discord.utils.get(roles, id=config['leaderRole'])
        self.server = server
        self.admin = admin
        self.leader = leader

    @commands.command(pass_context=True, aliases=['act', 'active'])
    async def activity(self, ctx, *rankNames):
        '''
        Notes rank activity on admin sheets (Admin+).
        Arguments: names
        Surround names containing spaces with quotation marks, e.g.: "name with spaces".
        '''
        await self.bot.send_typing(ctx.message.channel)
        msg = ctx.message
        user = msg.author
        roles = user.roles
        channel = msg.channel
        server = msg.server
        userName = user.nick
        if not userName:
            userName = user.name
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
        if not rankNames:
            await self.bot.say('Please add the rank(s) for whom you want to note activity on the sheets as argument(s).')
            return
        for name in rankNames:
            if name.upper() in userName.upper():
                await self.bot.say('Sorry, you cannot track your own activity.')
                return
        month = datetime.utcnow().strftime("%B")
        try:
            sheetMonth = sheet.cell(3, 1).value
        except:
            regen()
            sheetMonth = sheet.cell(3, 1).value
        if month.upper().strip() != sheetMonth.upper().strip():
            await self.bot.say(f'Sorry, the admin sheets have not been updated to the current month yet. Please wait for a Leader to finish doing upkeep.')
            return
        try:
            ranks = sheet.col_values(1)[headerRows:]
        except:
            regen()
            ranks = sheet.col_values(1)[headerRows:]
        for i, rank in enumerate(ranks):
            if rank is None or not rank:
                ranks = ranks[:i]
                break
        timestamp = datetime.utcnow().strftime("%#d")
        for name in rankNames:
            row = 0
            for i, rank in enumerate(ranks):
                if rank in rankTitles:
                    continue
                if name.upper() in rank.upper():
                    row = i + headerRows + 1
                    name = rank
                    break
            if not row:
                await self.bot.say(f'Sorry, I could not find a rank by the name **{name}**.')
                continue
            try:
                activity = sheet.row_values(row)[3:34]
            except:
                regen()
                activity = sheet.row_values(row)[3:34]
            activity = list(filter(bool, activity))
            if timestamp in activity:
                await self.bot.say(f'**{name}** has already been noted as active for today.')
                continue
            col = 4 + len(activity)
            try:
                sheet.update_cell(row, col, timestamp)
            except:
                regen()
                sheet.update_cell(row, col, timestamp)
            await self.bot.say(f'**{name}** has been noted as active for **{timestamp}** **{datetime.utcnow().strftime("%b")}**.')

    @commands.command(pass_context=True, aliases=['sheetactive', 'sheetact', 'shact', 'shactive', 'shactivity'])
    async def sheetactivity(self, ctx, *rankNames):
        '''
        Notes rank sheet activity on admin sheets (Admin+).
        Arguments: names
        Surround names containing spaces with quotation marks, e.g.: "name with spaces".
        Also notes FC activity.
        '''
        await self.bot.send_typing(ctx.message.channel)
        msg = ctx.message
        user = msg.author
        roles = user.roles
        channel = msg.channel
        server = msg.server
        userName = user.nick
        if not userName:
            userName = user.name
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
        if not rankNames:
            await self.bot.say('Please add the rank(s) for whom you want to note activity on the sheets as argument(s).')
            return
        for name in rankNames:
            if name.upper() in userName.upper():
                await self.bot.say('Sorry, you cannot track your own activity.')
                return
        month = datetime.utcnow().strftime("%B")
        try:
            sheetMonth = sheet.cell(3, 1).value
        except:
            regen()
            sheetMonth = sheet.cell(3, 1).value
        if month != sheetMonth:
            await self.bot.say(f'Sorry, the admin sheets have not been updated to the current month yet. Please wait for a Leader to finish doing upkeep.')
            return
        try:
            ranks = sheet.col_values(1)[headerRows:]
        except:
            regen()
            ranks = sheet.col_values(1)[headerRows:]
        for i, rank in enumerate(ranks):
            if rank is None or not rank:
                ranks = ranks[:i]
                break
        timestamp = datetime.utcnow().strftime("%#d")
        for name in rankNames:
            row = 0
            for i, rank in enumerate(ranks):
                if rank in rankTitles:
                    continue
                if name.upper() in rank.upper():
                    row = i + headerRows + 1
                    name = rank
                    break
            if not row:
                await self.bot.say(f'Sorry, I could not find a rank by the name **{name}**.')
                continue
            try:
                activity = sheet.row_values(row)
                sheetActivity = activity[34:65]
                activity = activity[3:34]
            except:
                regen()
                activity = sheet.row_values(row)
                sheetActivity = activity[34:65]
                activity = activity[3:34]
            sheetActivity = list(filter(bool, sheetActivity))
            activity = list(filter(bool, activity))
            if timestamp in sheetActivity:
                await self.bot.say(f'**{name}** has already been noted as active on sheets for today.')
                continue
            active = False
            if timestamp in activity:
                active = True
            activityCol = 4 + len(activity)
            sheetCol = 35 + len(sheetActivity)
            try:
                sheet.update_cell(row, sheetCol, timestamp)
                if not active:
                    sheet.update_cell(row, activityCol, timestamp)
            except:
                regen()
                sheet.update_cell(row, sheetCol, timestamp)
                if not active:
                    sheet.update_cell(row, activityCol, timestamp)
            await self.bot.say(f'**{name}** has been noted as active on sheets for **{timestamp}** **{datetime.utcnow().strftime("%b")}**.')

def setup(bot):
    bot.add_cog(adminSheets(bot))
