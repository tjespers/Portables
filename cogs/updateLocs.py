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

sheet = client.open(config['sheetName']).sheet1

locations = ["CA", "LC", "BA", "SP", "BU", "CW", "PRIF", "MG", "VIP", "GE", "MEI", "TRA"]
portablesNames = ['Fletcher', 'Crafter', 'Brazier', 'Sawmill', 'Forge', 'Range', 'Well']
locs = 'CA, LC, BA, SP, BU, CW, PRIF, MG, VIP, GE, MEI, TRA'
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

def getPorts(input):
    input = input.upper().replace('F2P', '').strip()

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

    portsCopy = copy.deepcopy(ports)
    duplicates = []
    # Add worlds from duplicate locations to the first occurrence of the location
    for i, port1 in enumerate(portsCopy):
        loc1 = port1[1]
        for j, port2 in enumerate(portsCopy):
            if j <= i:
                continue
            loc2 = port2[1]
            if loc1 == loc2:
                for world in portsCopy[j][0]:
                    portsCopy[i][0].append(world)
                if not j in duplicates:
                    duplicates.append(j)

    # Delete duplicate locations
    duplicates.sort(reverse=True)
    for i in duplicates:
        del portsCopy[i]

    # Remove duplicates from arrays of worlds and sort worlds
    for i, port in enumerate(portsCopy):
        portsCopy[i][0] = sorted(list(set(port[0])))

    return portsCopy


def addPort(world, loc, ports):
    newPorts = copy.deepcopy(ports)
    for i, port in enumerate(newPorts):
        if port[1] == loc:
            if world in newPorts[i][0]:
                return newPorts
            newPorts[i][0].append(world)
            newPorts[i][0].sort()
            return newPorts
    newPorts.append([[world], loc])
    return newPorts

def addPorts(current, new):
    ports = copy.deepcopy(current)
    for port in new:
        loc = port[1]
        for world in port[0]:
            ports = addPort(world, loc, ports)
    return ports

def removePort(world, loc, ports):
    newPorts = copy.deepcopy(ports)
    for i, port in enumerate(newPorts):
        if port[1] == loc:
            if world in newPorts[i][0]:
                newPorts[i][0].remove(world)
                if not newPorts[i][0]:
                    del newPorts[i]
                return newPorts
    return newPorts

def removePorts(current, old):
    ports = copy.deepcopy(current)
    for port in old:
        loc = port[1]
        for world in port[0]:
            ports = removePort(world, loc, ports)
    return ports

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
        if txt:
            txt += ' | '
        txt += 'F2P '
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

    txt = txt.replace('PRIF', 'Prif').replace('MEI', 'Meilyr').replace('TRA', 'Trahaearn')

    return txt


class updateLocs:
    def __init__(self, bot):
        self.bot = bot
        server = bot.get_server(config['portablesServer'])
        channel = bot.get_channel(config['locationChannel'])
        roles = server.roles
        smiley = discord.utils.get(roles, id=config['smileyRole'])
        rank = discord.utils.get(roles, id=config['rankRole'])
        self.server = server
        self.channel = channel
        self.smiley = smiley
        self.rank = rank

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
    async def add(self, ctx):
        """
        Add portable locations (Smiley+).
        """
        addCommand()
        portables = self.server
        locChannel = self.channel
        msg = ctx.message
        if msg.server != portables:
            await self.bot.say(f'Sorry, this command can only be used in the Portables server:\nhttps://discord.gg/QhBCYYr')
            return
        if msg.channel != locChannel:
            await self.bot.say(f'Sorry, this command can only be used in the channel <#{locChannel.id}>.')
            return
        smiley = self.smiley
        user = ctx.message.author
        role = user.top_role
        if not role >= smiley:
            await self.bot.say(f'Sorry, only Smileys and above have permission to use this command.')
            return
        input = msg.content.upper().replace(f'{prefix[0]}ADD', '').replace('F2P', '').strip()
        if not input:
            await self.bot.say(f'Please add a portable, world, and location to your command. Example: `{prefix[0]}add brazier 100 sp`.')
            return

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
        input = input.replace('FORGE', '').replace('RANGE', '')
        newPorts = getPorts(input)

        if not newPorts:
            await self.bot.say(f'Sorry, your command did not contain any valid locations.')
            return

        try:
            ports = sheet.row_values(21)[:7]
        except:
            regen()
            ports = sheet.row_values(21)[:7]

        val = ports[col-1]
        ports[col-1] = ""

        for port in newPorts:
            loc = port[1]
            for world in port[0]:
                if world < 1 or world > highestWorld:
                    await self.bot.say(f'Sorry, **{str(world)}** is not a valid world. Please enter a number between 1 and 141.')
                    return
                if world in forbiddenWorlds:
                    await self.bot.say(f'Sorry, world **{str(world)}** is not called because it is either a pking world or a bounty hunter world, or it is not on the world list.')
                    return
                for forbiddenLoc in forbiddenLocs:
                    if world == forbiddenLoc[0] and loc == forbiddenLoc[1]:
                        await self.bot.say(f'Sorry, **{str(world)} {loc}** is a forbidden location.')
                        return
                if loc == 'GE' and world not in f2pWorlds:
                    await self.bot.say('Sorry, we only call the location **GE** in F2P worlds.')
                    return
                portNames = []
                count = 0
                i = 0
                for p in ports:
                    i += 1
                    if loc in p:
                        txt = p.split(loc, 1)[0]
                        for l in locations:
                            if l in txt:
                                txt = txt.split(l, 1)[1]
                        if str(world) in txt:
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
                    await self.bot.say(f'Sorry, there cannot be more than 3 portables at the same location.\nThe location **{str(world)} {loc}** already has a {msgPorts}.')
                    return

        newPortsText = format(newPorts).replace('*', '\*')
        currentPorts = getPorts(val)
        sumPorts = addPorts(currentPorts, newPorts)
        newVal = format(sumPorts)

        timestamp = datetime.utcnow().strftime("%#d %b, %#H:%M")

        isRank = False
        if self.rank in user.roles:
            isRank = True
            name = user.nick
            if not name:
                name = user.name
            name = re.sub('[^A-z0-9 -]', '', name).replace('`', '')

        try:
            sheet.update_cell(21, col, newVal)
            sheet.update_cell(31+col, 2, newVal)
            sheet.update_cell(22, 3, timestamp)
            if isRank:
                sheet.update_cell(22, 5, name)
                sheet.update_cell(39, 2, name)
        except:
            regen()
            sheet.update_cell(21, col, newVal)
            sheet.update_cell(31+col, 2, newVal)
            sheet.update_cell(22, 3, timestamp)
            if isRank:
                sheet.update_cell(22, 5, name)
                sheet.update_cell(39, 2, name)

        await self.bot.say(f'The **{portable}** location\(s\) **{newPortsText}** have been added to the Portables sheet.')
        return

    @commands.command(pass_context=True)
    async def remove(self, ctx):
        """
        Remove portable locations (Smiley+).
        """
        addCommand()
        portables = self.server
        locChannel = self.channel
        msg = ctx.message
        if msg.server != portables:
            await self.bot.say(f'Sorry, this command can only be used in the Portables server:\nhttps://discord.gg/QhBCYYr')
            return
        if msg.channel != locChannel:
            await self.bot.say(f'Sorry, this command can only be used in the channel <#{locChannel.id}>.')
            return
        smiley = self.smiley
        user = ctx.message.author
        role = user.top_role
        if not role >= smiley:
            await self.bot.say(f'Sorry, only Smileys and above have permission to use this command.')
            return
        input = msg.content
        input = input.replace(f'{prefix[0]}remove', '').strip()
        input = input.upper()
        input = input.replace('F2P', '').strip()
        if not input:
            await self.bot.say(f'Please add a portable, world, and location to your command. Example: `{prefix[0]}remove brazier 100 sp`.')
            return
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
        input = input.replace('FORGE', '')
        input = input.replace('RANGE', '')
        oldPorts = getPorts(input)

        if not oldPorts:
            await self.bot.say(f'Sorry, your command did not contain any valid locations.')
            return

        for port in oldPorts:
            loc = port[1]
            for world in port[0]:
                if world < 1:
                    await self.bot.say(f'Sorry, **{str(world)}** is not a valid world. Please enter a positive integer.')
                    return

        try:
            val = sheet.cell(21, col).value
        except:
            regen()
            val = sheet.cell(21, col).value

        oldPortsText = format(oldPorts).replace('*', '\*')
        currentPorts = getPorts(val)
        difPorts = removePorts(currentPorts, oldPorts)
        newVal = format(difPorts)

        timestamp = datetime.utcnow().strftime("%#d %b, %#H:%M")

        isRank = False
        if self.rank in user.roles:
            isRank = True
            name = user.nick
            if not name:
                name = user.name
            name = re.sub('[^A-z0-9 -]', '', name)
            name = name.replace('`', '')

        try:
            sheet.update_cell(21, col, newVal)
            sheet.update_cell(31+col, 2, newVal)
            sheet.update_cell(22, 3, timestamp)
            if isRank:
                sheet.update_cell(22, 5, name)
                sheet.update_cell(39, 2, name)
        except:
            regen()
            sheet.update_cell(21, col, newVal)
            sheet.update_cell(31+col, 2, newVal)
            sheet.update_cell(22, 3, timestamp)
            if isRank:
                sheet.update_cell(22, 5, name)
                sheet.update_cell(39, 2, name)

        await self.bot.say(f'The **{portable}** location\(s\) **{oldPortsText}** have been removed from the Portables sheet.')
        return

def setup(bot):
    bot.add_cog(updateLocs(bot))
