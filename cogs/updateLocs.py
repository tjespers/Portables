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

config = config_load()

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('data/gspread.json', scope)
client = gspread.authorize(creds)

sheet = client.open(config['sheetName']).sheet1

locations = ["CA", "BE", "BA", "SP", "BU", "CW", "PRIF", "MG", "VIP", "GE", "ITH", "MEI", "TRA"]
portablesNames = ['Fletcher', 'Crafter', 'Brazier', 'Sawmill', 'Forge', 'Range', 'Well']
locs = 'CA, BE, BA, SP, BU, CW, PRIF, MG, VIP, GE, ITH, MEI, TRA'

def regen():
    global creds
    global client
    global sheet
    creds = ServiceAccountCredentials.from_json_keyfile_name('data/gspread.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open(config['sheetName']).sheet1

def hasNumbers(inputString):
    return bool(re.search(r'\d', inputString))

def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def GE_there(s):
    return min(s.count('GE') - s.count('RGE') > 0, s.count('GE') - s.count('NGE') > 0)

class updateLocs:
    def __init__(self, bot):
        self.bot = bot
        server = bot.get_server(config['portablesServer'])
        channel = bot.get_channel(config['locationChannel'])
        roles = server.roles
        smiley = roles[0]
        for role in roles:
            if role.name == "Smiley":
                smiley = role
                break
        self.server = server
        self.channel = channel
        self.smiley = smiley

    @commands.command(pass_context=True)
    async def regenLocs(self, ctx):
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
    async def add(self, ctx, *inputString):
        """
        A command to add portable locations (Smiley+).
        """
        addCommand()
        portables = self.server
        locChannel = self.channel
        if ctx.message.server != portables:
            await self.bot.say(f'Sorry, this command can only be used in the Portables server:\nhttps://discord.gg/QhBCYYr')
            return
        if ctx.message.channel != locChannel:
            await self.bot.say(f'Sorry, this command can only be used in the channel <#{locChannel.id}>.')
            return
        smiley = self.smiley
        user = ctx.message.author
        role = user.top_role
        if not role >= smiley:
            await self.bot.say(f'Sorry, only Smileys and above have permission to use this command.')
            return
        if not inputString:
            await self.bot.say(f'Please add a portable, world, and location to your command. Example: `{prefix[0]}add brazier 100 sp`.')
            return
        input = ""
        for word in inputString:
            input += word
        input = input.upper()
        portable = ""
        if 'FL' in input:
            portable = 'fletcher'
            col = 1
        elif 'CR' in input or (input.startswith('C') and not (input.startswith('CA') or input.startswith('CW'))):
            portable = 'crafter'
            col = 2
        elif 'BR' in input or (input.startswith('B') and not (input.startswith('BE') or input.startswith('BA') or input.startswith('BU'))):
            portable = 'brazier'
            col = 3
        elif 'SAW' in input or 'MIL' in input or (input.startswith('M') and not (input.startswith('MG') or input.startswith('MEI'))) or input.startswith('S'):
            portable = 'sawmill'
            col = 4
        elif 'FO' in input:
            portable = 'forge'
            col = 5
        elif 'RAN' in input or input.startswith('R'):
            portable = 'range'
            col = 6
        elif 'WEL' in input or input.startswith('W'):
            portable = 'well'
            col = 7
        else:
            await self.bot.say(f'Sorry, your command did not contain a valid portable. Please choose one of the following: fletcher, crafter, brazier, sawmill, forge, range, well.')
            return
        world = ''.join(filter(str.isdigit, input))
        if not RepresentsInt(world):
            await self.bot.say(f'Sorry, your command did not contain a valid world. Please enter a number between 1 and 141.')
            return
        worldNum = int(world)
        if not worldNum >= 0 or not worldNum <= 141:
            await self.bot.say(f'Sorry, **{world}** is not a valid world. Please enter a number between 1 and 141.')
            return
        loc = ""
        for l in locations:
            if l == 'GE':
                if GE_there(input):
                    loc = l
                    break
            elif l in input:
                loc = l
                break
        if not loc:
            await self.bot.say(f'Sorry, your command did not contain a valid location. Please choose one of the following: {locs}.')
            return
        if loc == "ITH":
            loc = "Ithell"
        elif loc == "MEI":
            loc = "Meilyr"
        elif loc == "TRA":
            loc = "Trahaearn"

        try:
            val = sheet.cell(21, col).value
        except:
            regen()
            val = sheet.cell(21, col).value

        cols = [1, 2, 3, 4, 5, 6, 7]
        ports = []
        try:
            for c in cols:
                if c == col:
                    ports.append("")
                    continue
                else:
                    ports.append(sheet.cell(21, c).value.upper())
        except:
            regen()
            for c in cols:
                if c == col:
                    ports.append("")
                    continue
                else:
                    ports.append(sheet.cell(21, c).value.upper())
        portNames = []
        count = 0
        i = 0
        for port in ports:
            i += 1
            if loc in port:
                txt = port.split(loc, 1)[0]
                for l in locations:
                    if l in txt:
                        txt = txt.split(l, 1)[1]
                if world in txt:
                    portNames.append(portablesNames[i-1])
                    count += 1

        if count >= 3:
            msgPorts = ""
            i = 0
            for p in portNames:
                i += 1
                msgPorts += '**' + p + '**'
                if i < len(portNames):
                    msgPorts += ", "
                    if i == len(portNames) - 1:
                        msgPorts += "and "
            await self.bot.say(f'Sorry, there cannot be more than 3 portables at the same location.\nThe location **{world} {loc}** already has a {msgPorts}.')
            return

        try:
            val = sheet.cell(21, col).value
            newVal = val + f' {world} {loc}'
            sheet.update_cell(21, col, newVal)
            sheet.update_cell(18, 8, '1')
        except:
            regen()
            val = sheet.cell(21, col).value
            newVal = val + f' {world} {loc}'
            sheet.update_cell(21, col, newVal)
            sheet.update_cell(18, 8, '1')

        await self.bot.say(f'The **{portable}** location **{world} {loc}** has been added to the Portables sheet.')
        return

    @commands.command(pass_context=True)
    async def remove(self, ctx, *inputString):
        """
        A command to remove portable locations (Smiley+).
        """
        addCommand()
        portables = self.server
        locChannel = self.channel
        if ctx.message.server != portables:
            await self.bot.say(f'Sorry, this command can only be used in the Portables server:\nhttps://discord.gg/QhBCYYr')
            return
        if ctx.message.channel != locChannel:
            await self.bot.say(f'Sorry, this command can only be used in the channel <#{locChannel.id}>.')
            return
        smiley = self.smiley
        user = ctx.message.author
        role = user.top_role
        if not role >= smiley:
            await self.bot.say(f'Sorry, only Smileys and above have permission to use this command.')
            return
        if not inputString:
            await self.bot.say(f'Please add a portable, world, and location to your command. Example: `{prefix[0]}remove brazier 100 sp`.')
            return
        input = ""
        for word in inputString:
            input += word
        input = input.upper()
        portable = ""
        if 'FL' in input:
            portable = 'fletcher'
            col = 1
        elif 'CR' in input or (input.startswith('C') and not (input.startswith('CA') or input.startswith('CW'))):
            portable = 'crafter'
            col = 2
        elif 'BR' in input or (input.startswith('B') and not (input.startswith('BE') or input.startswith('BA') or input.startswith('BU'))):
            portable = 'brazier'
            col = 3
        elif 'SAW' in input or 'MIL' in input or (input.startswith('M') and not (input.startswith('MG') or input.startswith('MEI'))) or input.startswith('S'):
            portable = 'sawmill'
            col = 4
        elif 'FO' in input:
            portable = 'forge'
            col = 5
        elif 'RAN' in input or input.startswith('R'):
            portable = 'range'
            col = 6
        elif 'WEL' in input or input.startswith('W'):
            portable = 'well'
            col = 7
        else:
            await self.bot.say(f'Sorry, your command did not contain a valid portable. Please choose one of the following: fletcher, crafter, brazier, sawmill, forge, range, well.')
            return
        world = ''.join(filter(str.isdigit, input))
        if not RepresentsInt(world):
            await self.bot.say(f'Sorry, your command did not contain a valid world. Please enter a number between 1 and 141.')
            return
        worldNum = int(world)
        if not worldNum >= 0 or not worldNum <= 141:
            await self.bot.say(f'Sorry, **{world}** is not a valid world. Please enter a number between 1 and 141.')
            return
        loc = ""
        for l in locations:
            if l == 'GE':
                if GE_there(input):
                    loc = l
                    break
            elif l in input:
                loc = l
                break
        if not loc:
            await self.bot.say(f'Sorry, your command did not contain a valid location. Please choose one of the following: {locs}.')
            return
        if loc == "ITH":
            loc = "Ithell"
        elif loc == "MEI":
            loc = "Meilyr"
        elif loc == "TRA":
            loc = "Trahaearn"

        try:
            val = sheet.cell(21, col).value
        except:
            regen()
            val = sheet.cell(21, col).value

        values = val.split(loc)
        newValues = []
        for val in values:
            val = val.replace(loc, '')
            if val != values[len(values)-1]:
                val += loc
            newValues.append(val)
        values = newValues
        newValues = []
        if (len(values) == 1 or (len(values) == 2 and not values[len(values)-1])) and not (world in values[0] and loc in values[0]):
            if not val:
                val = f'N/A'
            await self.bot.say(f'Sorry, I could not find the location that you are trying to remove: **{world} {loc}**. The current locations are: **{val}**.')
            return
        else:
            for val in values:
                val = val.replace(loc, '')
                newValues.append(val)
            values = newValues
            newValues = []
            for value in values:
                if value != values[len(values)-1]:
                    preVal = ""
                    maxLetter = -1
                    length = 0
                    for l in locations:
                        index = value.rfind(l)
                        if index > maxLetter:
                            maxLetter = index
                            length = len(l)
                    if maxLetter != -1:
                        preVal = value[:maxLetter+length]
                        value = value[maxLetter+length:]
                    value += loc
                    if preVal:
                        newValues.append(preVal)
                    newValues.append(value)
                else:
                    newValues.append(value)
        values = newValues
        newValues = []
        for value in values:
            if loc in value:
                value = " " + value
                value = value.replace(" "+world+" ", "")
                value = value.replace(" "+world+"*", "")
                value = value.replace(" "+world+",", "")
                value = value.replace(", *", "")
                value = value.replace(",  ", " ")
                value = value.replace(", ,", ",")
                value = '~' + value
                value = value.replace("~, ", "")
                value = value.replace("~", "")
                newValues.append(value)
            else:
                newValues.append(value)
        values = newValues
        newVal = ""
        for value in values:
            if hasNumbers(value):
                newVal += value

        try:
            sheet.update_cell(21, col, newVal)
            sheet.update_cell(18, 8, '1')
        except:
            regen()
            sheet.update_cell(21, col, newVal)
            sheet.update_cell(18, 8, '1')

        await self.bot.say(f'The **{portable}** location **{world} {loc}** has been removed from the Portables sheet.')
        return

def setup(bot):
    bot.add_cog(updateLocs(bot))
