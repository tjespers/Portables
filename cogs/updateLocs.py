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

config = config_load()

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('data/gspread.json', scope)
client = gspread.authorize(creds)

sheet = client.open(config['sheetName']).sheet1

locations = ["CA", "BE", "BA", "SP", "BU", "CW", "PRIF", "MG", "VIP", "GE", "ITH", "MEI", "TRA"]
portablesNames = ['Fletcher', 'Crafter', 'Brazier', 'Sawmill', 'Forge', 'Range', 'Well']
locs = 'CA, BE, BA, SP, BU, CW, PRIF, MG, VIP, GE, ITH, MEI, TRA'
busyLocs = [[84, "CA"], [99, "CA"], [100, "SP"]]
forbiddenLocs = [[2, "BU"]]
highestWorld = 141
forbiddenWorlds = [18, 33, 47, 55, 75, 90, 93, 94, 95, 97, 101, 102, 106, 107, 109, 110, 111, 112, 113, 118, 121, 122, 125, 126, 127, 128, 129, 130, 131, 132, 133]
f2pWorlds = [3, 7, 8, 11, 17, 19, 20, 29, 33, 34, 38, 41, 43, 57, 61, 80, 81, 108, 120, 135, 136, 141]
totalWorlds = [[86, " (1500+)"], [114, " (1500+)"], [30, " (2000+)"], [48, " (2600+)"]]

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

def getPorts(input):

    input = input.upper()

    # Get indices of all occurrences of locations
    indices = []
    for loc in locations:
        i = [m.start() for m in re.finditer(loc, input)] # https://stackoverflow.com/questions/4664850/find-all-occurrences-of-a-substring-in-python
        if i:
            for index in i:
                indices.append([loc, index])
    indices.sort(key=lambda x: x[1]) # https://stackoverflow.com/questions/17555218/python-how-to-sort-a-list-of-lists-by-the-fourth-element-in-each-list

    # Fill array ports with [worlds, location] for every location
    ports = []
    i = -1
    for index in indices:
        i += 1
        beginIndex = 0
        if i:
            beginIndex = indices[i-1][1]
        endIndex = index[1]
        substring = input[beginIndex:endIndex]
        worlds = [int(s) for s in re.findall(r'\d+', substring)] # https://stackoverflow.com/questions/4289331/python-extract-numbers-from-a-string
        ports.append([worlds, indices[i][0]])

    portsCopy = ports
    duplicates = []
    # Add worlds from duplicate locations to the first occurrence of the location
    for i, port1 in enumerate(ports):
        loc1 = port1[1]
        for j, port2 in enumerate(ports):
            if j <= i:
                continue
            loc2 = port2[1]
            if loc1 == loc2:
                for world in portsCopy[j][0]:
                    portsCopy[i][0].append(world)
                if not i+j in duplicates:
                    duplicates.append(i+j)

    # Delete duplicate locations
    duplicates.sort(reverse=True)
    for i in duplicates:
        del portsCopy[i]

    # Remove duplicates from arrays of worlds and sort worlds
    for i, port in enumerate(portsCopy):
        portsCopy[i][0] = sorted(list(set(port[0])))

    return portsCopy


def addPort(world, loc, ports):
    for i, port in enumerate(ports):
        if port[1] == loc:
            if world in ports[i][0]:
                return []
            ports[i][0].append(world)
            ports[i][0].sort()
            return ports
    ports.append([[world], loc])
    return ports

def removePort(world, loc, ports):
    for i, port in enumerate(ports):
        if port[1] == loc:
            if world in ports[i][0]:
                ports[i][0].remove(world)
                if not ports[i][0]:
                    del ports[i]
                return ports
    return None

def format(ports):
    txt = ""
    f2pPorts = []
    for i, port in enumerate(ports):
        worlds = port[0]
        loc = port[1]
        count = -1
        f2pLocs = []
        for w in worlds:
            if w in f2pWorlds:
                f2pLocs.append(w)
            else:
                count += 1
                if count:
                    txt += ', '
                elif txt:
                    txt += ' | '
                txt += str(w)
                for busyLoc in busyLocs:
                    if w == busyLoc[0] and loc == busyLoc[1]:
                        txt += '*'
                        break
                for totalWorld in totalWorlds:
                    if w == totalWorld[0]:
                        txt += totalWorld[1]
                        break
        if count+1:
            txt += ' ' + loc
        if f2pLocs:
            f2pPorts.append([f2pLocs, loc])

    if f2pPorts:
        txt += ' | F2P '
        for i, port in enumerate(f2pPorts):
            worlds = port[0]
            loc = port[1]
            count = -1
            for w in worlds:
                count += 1
                if count:
                    txt += ', '
                elif i > 0:
                    txt += ' | '
                txt += str(w)
                for busyLoc in busyLocs:
                    if w == busyLoc[0] and loc == busyLoc[1]:
                        txt += '*'
                        break
                for totalWorld in totalWorlds:
                    if w == totalWorld[0]:
                        txt += totalWorld[1]
                        break
            if count+1:
                txt += ' ' + loc

    if not txt:
        return 'N/A'

    txt.replace('PRIF', 'Prif')
    txt.replace('ITH', 'Ithell')
    txt.replace('MEI', 'Meilyr')
    txt.replace('TRA', 'Trahaearn')

    return txt



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
        Add portable locations (Smiley+).
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
        input = input.replace('F2P', '').strip()
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
        if not worldNum >= 0 or not worldNum <= highestWorld:
            await self.bot.say(f'Sorry, **{world}** is not a valid world. Please enter a number between 1 and 141.')
            return
        if int(world) in forbiddenWorlds:
            await self.bot.say(f'Sorry, world **{world}** is not called because it is either a pking world or a bounty hunter world, or it is not on the world list.')
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
        for forbiddenLoc in forbiddenLocs:
            if int(world) == forbiddenLoc[0] and loc == forbiddenLoc[1]:
                await self.bot.say(f'Sorry, **{world} {loc}** is a forbidden location.')
                return
        if loc == 'GE' and int(world) not in f2pWorlds:
            await self.bot.say('Sorry, we only call the location **GE** in F2P worlds.')
            return

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

        ports = getPorts(val)
        newPorts = addPort(int(world), loc, ports)
        if not newPorts:
            await self.bot.say(f'The **{portable}** at  **{world} {loc}** is already on the sheets.')
            return
        newVal = format(newPorts)

        timestamp = datetime.utcnow().strftime("%#d %b, %#H:%M")

        try:
            sheet.update_cell(21, col, newVal)
            sheet.update_cell(31+col, 2, newVal)
            sheet.update_cell(22, 3, timestamp)
        except:
            regen()
            sheet.update_cell(21, col, newVal)
            sheet.update_cell(31+col, 2, newVal)
            sheet.update_cell(22, 3, timestamp)

        await self.bot.say(f'The **{portable}** location **{world} {loc}** has been added to the Portables sheet.')
        return

    @commands.command(pass_context=True)
    async def remove(self, ctx, *inputString):
        """
        Remove portable locations (Smiley+).
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
        input = input.replace('F2P', '').strip()
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

        try:
            val = sheet.cell(21, col).value
        except:
            regen()
            val = sheet.cell(21, col).value

        ports = getPorts(val)
        newPorts = removePort(int(world), loc, ports)

        if newPorts is None:
            if not val:
                val = f'N/A'
            await self.bot.say(f'Sorry, I could not find the location that you are trying to remove: **{world} {loc}**. The current locations are: **{val}**.')
            return

        newVal = format(newPorts)

        timestamp = datetime.utcnow().strftime("%#d %b, %#H:%M")

        try:
            sheet.update_cell(21, col, newVal)
            sheet.update_cell(31+col, 2, newVal)
            sheet.update_cell(22, 3, timestamp)
        except:
            regen()
            sheet.update_cell(21, col, newVal)
            sheet.update_cell(31+col, 2, newVal)
            sheet.update_cell(22, 3, timestamp)

        await self.bot.say(f'The **{portable}** location **{world} {loc}** has been removed from the Portables sheet.')
        return

def setup(bot):
    bot.add_cog(updateLocs(bot))
