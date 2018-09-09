import discord
from discord.ext import commands
import os
from sys import exit
from subprocess import call
import sys
sys.path.append('../')
from main import config_load
from main import prefix
from datetime import datetime, timedelta, timezone
import html
import re
from main import addCommand
from main import timeDiffToString

config = config_load()

pattern = re.compile('[\W_]+')

def isName(memberName, member):
    name = member.nick
    if not name:
        name = member.name
    name = name.upper()
    if memberName in pattern.sub('', name):
        return True
    else:
        return False

class ModCommands:
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.utcnow()
        server = bot.get_server(config['portablesServer'])
        self.server = server

    @commands.command(pass_context=True)
    async def kick(self, ctx, *memberNames):
        '''
        Kicks the given user(s) (Admin+).
        '''
        addCommand()
        msg = ctx.message
        user = msg.author
        roles = user.roles
        channel = msg.channel
        server = msg.server
        isAdmin = False
        for r in roles:
            if r.id == config['adminRole'] or user.id == config['owner']:
                isAdmin = True
                adminRole = r
                break
        if not isAdmin:
            await self.bot.say('Sorry, this command can only be used by Admins and above.')
            return
        isLeader = False
        for r in roles:
            if r.id == config['leaderRole'] or user.id == config['owner']:
                isLeader = True
                break
        if len(msg.mentions) < 1 and not memberNames:
            await self.bot.say('Please mention the user(s) who you want to kick.')
            return
        members = msg.mentions
        if not members:
            if memberNames:
                for memberName in memberNames:
                    memberName = pattern.sub('', memberName).upper()
                    member = discord.utils.find(lambda m: isName(memberName, m), server.members)
                    if not member:
                        await self.bot.say(f'Sorry, I could not find a user by the name **{memberName}**.')
                        continue
                    members.append(member)
        for member in members:
            if member.top_role >= adminRole and not isLeader:
                await self.bot.say(f'Sorry, you do not have sufficient permissions to kick **{member.name}**.')
            try:
                await self.bot.kick(member)
                await self.bot.say(f'I have kicked **{member.name}**')
            except discord.Forbidden:
                await self.bot.say(f'Sorry, I do not have permission to kick **{member.name}**.')

    @commands.command(pass_context=True)
    async def ban(self, ctx, *memberNames):
        '''
        Bans the given user(s) (Admin+).
        '''
        addCommand()
        msg = ctx.message
        user = msg.author
        roles = user.roles
        channel = msg.channel
        server = msg.server
        isAdmin = False
        for r in roles:
            if r.id == config['adminRole'] or user.id == config['owner']:
                isAdmin = True
                adminRole = r
                break
        if not isAdmin:
            await self.bot.say('Sorry, this command can only be used by Admins and above.')
            return
        isLeader = False
        for r in roles:
            if r.id == config['leaderRole'] or user.id == config['owner']:
                isLeader = True
                break
        if len(msg.mentions) < 1 and not memberNames:
            await self.bot.say('Please mention the user(s) who you want to ban.')
            return
        members = msg.mentions
        if not members:
            if memberNames:
                for memberName in memberNames:
                    memberName = pattern.sub('', memberName).upper()
                    member = discord.utils.find(lambda m: isName(memberName, m), server.members)
                    if not member:
                        await self.bot.say(f'Sorry, I could not find a user by the name **{memberName}**.')
                        continue
                    members.append(member)
        for member in members:
            if member.top_role >= adminRole and not isLeader:
                await self.bot.say(f'Sorry, you do not have sufficient permissions to ban **{member.name}**.')
            try:
                await self.bot.ban(member)
                await self.bot.say(f'I have banned **{member.name}**')
            except discord.Forbidden:
                await self.bot.say(f'Sorry, I do not have permission to ban **{member.name}**.')

    @commands.command(pass_context=True)
    async def purge(self, ctx, num=0):
        '''
        Deletes given amount of messages (Admin+).
        '''
        addCommand()
        msg = ctx.message
        user = msg.author
        roles = user.roles
        channel = msg.channel
        isAdmin = False
        for r in roles:
            if r.id == config['adminRole'] or user.id == config['owner']:
                isAdmin = True
                break
        if not isAdmin:
            await self.bot.say('Sorry, this command can only be used by Admins and above.')
            return
        if not num or num <1 or num > 100:
            await self.bot.say(f'Sorry, I cannot delete **{num}** messages, please enter a number between 1 and 100.')
            return
        await self.bot.delete_message(msg)
        await self.bot.purge_from(channel, limit=num)
        return

    @commands.command(pass_context=True)
    async def role(self, ctx, roleName="", *memberNames):
        '''
        Toggles the given role for the given user(s) (Admin+).
        '''
        addCommand()
        msg = ctx.message
        user = msg.author
        roles = user.roles
        channel = msg.channel
        server = msg.server
        isAdmin = False
        for r in roles:
            if r.id == config['adminRole'] or user.id == config['owner']:
                isAdmin = True
                adminRole = r
                break
        if not isAdmin:
            await self.bot.say('Sorry, this command can only be used by Admins and above.')
            return
        isLeader = False
        for r in roles:
            if r.id == config['leaderRole'] or user.id == config['owner']:
                isLeader = True
                break
        if not roleName:
            await self.bot.say(f'Please add a valid role name as an argument, such as: `{prefix[0]}role Rank user`.')
            return
        for r in server.roles:
            if r.name.upper() == roleName.upper():
                role = r
                break
        if not role:
            await self.bot.say(f'Sorry, I could not find the role **{roleName}**, please check that it is a valid role.')
            return
        if role >= adminRole and not isLeader:
            await self.bot.say(f'Sorry, you do not have permission to add/remove the role **{role.name}**, only Leaders have permission to do this.')
            return
        if len(msg.mentions) < 1 and not memberNames:
            await self.bot.say('Please mention the user(s) for whom you want to change the roles.')
            return
        members = msg.mentions
        if not members:
            if memberNames:
                for memberName in memberNames:
                    memberName = pattern.sub('', memberName).upper()
                    member = discord.utils.find(lambda m: isName(memberName, m), server.members)
                    if not member:
                        await self.bot.say(f'Sorry, I could not find a user by the name **{memberName}**.')
                        continue
                    members.append(member)
        for member in members:
            hasRole = False
            for r in member.roles:
                if r.name.upper() == roleName.upper():
                    hasRole = True
                    break
            if hasRole:
                try:
                    await self.bot.remove_roles(member, role)
                    await self.bot.say(f'**{member.name}** has been removed from role **{role.name}**.')
                except discord.Forbidden:
                    await self.bot.say(f'Sorry, I do not have permission to remove the role **{role.name}** from **{member.name}**.')
            else:
                try:
                    await self.bot.add_roles(member, role)
                    await self.bot.say(f'**{member.name}** has been given role **{role.name}**.')
                except discord.Forbidden:
                    await self.bot.say(f'Sorry, I do not have permission to add the role **{role.name}** to **{member.name}**.')

    @commands.command(pass_context=True)
    async def promote(self, ctx, *memberNames):
        '''
        Promotes the given user(s) (Admin+).
        '''
        addCommand()
        msg = ctx.message
        user = msg.author
        roles = user.roles
        channel = msg.channel
        server = msg.server
        isAdmin = False
        for r in roles:
            if r.id == config['adminRole'] or user.id == config['owner']:
                isAdmin = True
                break
        if not isAdmin:
            await self.bot.say('Sorry, this command can only be used by Admins and above.')
            return
        if len(msg.mentions) < 1 and not memberNames:
            await self.bot.say('Please mention the user(s) who you want to promote.')
            return
        members = msg.mentions
        if not members:
            if memberNames:
                for memberName in memberNames:
                    memberName = pattern.sub('', memberName).upper()
                    member = discord.utils.find(lambda m: isName(memberName, m), server.members)
                    if not member:
                        await self.bot.say(f'Sorry, I could not find a user by the name **{memberName}**.')
                        continue
                    members.append(member)
        isLeader = False
        for r in roles:
            if r.id == config['leaderRole'] or user.id == config['owner']:
                isLeader = True
                break
        txt = ""
        for r in server.roles:
            if r.id == config['smileyRole']:
                smileyRole = r
            if r.id == config['rankRole']:
                rankRole = r
            if r.id == config['editorRole']:
                editorRole = r
            if r.id == config['modRole']:
                modRole = r
            if r.id == config['adminRole']:
                adminRole = r
            if r.id == config['leaderRole']:
                leaderRole = r
        for m in members:
            roles = m.roles[1:] #get all except first role, because first role is always @everyone
            name = m.nick
            if not name:
                name = m.name
            if m.top_role < smileyRole:
                await self.bot.add_roles(m, smileyRole)
                txt += f'**{name}** has been promoted to **Smiley**.\n'
            elif m.top_role < rankRole:
                roles.append(rankRole)
                roles.append(editorRole)
                await self.bot.replace_roles(m, *roles)
                txt += f'**{name}** has been promoted to **Editor**.\n'
            elif m.top_role < modRole:
                roles.append(modRole)
                await self.bot.replace_roles(m, *roles)
                txt += f'**{name}** has been promoted to **Moderator**.\n'
            elif m.top_role < adminRole:
                if isLeader:
                    await self.bot.add_roles(m, adminRole)
                    txt += f'**{name}** has been promoted to **Admin**.\n'
                else:
                    await self.bot.say(f'Sorry, you need Leader permissions to promote **{name}** to **Admin**.')
            else:
                await self.bot.say(f'Sorry, I do not have sufficient permissions to promote **{name}**.')
        if txt:
            await self.bot.say(txt)
        return

    @commands.command(pass_context=True)
    async def demote(self, ctx, *memberNames):
        '''
        Demotes the given user(s) (Admin+).
        '''
        addCommand()
        msg = ctx.message
        user = msg.author
        roles = user.roles
        channel = msg.channel
        server = msg.server
        isAdmin = False
        for r in roles:
            if r.id == config['adminRole'] or user.id == config['owner']:
                isAdmin = True
                break
        if not isAdmin:
            await self.bot.say('Sorry, this command can only be used by Admins and above.')
            return
        if len(msg.mentions) < 1 and not memberNames:
            await self.bot.say('Please mention the user(s) who you want to demote.')
            return
        members = msg.mentions
        if not members:
            if memberNames:
                for memberName in memberNames:
                    memberName = pattern.sub('', memberName).upper()
                    member = discord.utils.find(lambda m: isName(memberName, m), server.members)
                    if not member:
                        await self.bot.say(f'Sorry, I could not find a user by the name **{memberName}**.')
                        continue
                    members.append(member)
        isLeader = False
        for r in roles:
            if r.id == config['leaderRole'] or user.id == config['owner']:
                isLeader = True
                break
        txt = ""
        for r in server.roles:
            if r.id == config['smileyRole']:
                smileyRole = r
            if r.id == config['vetRole']:
                vetRole = r
            if r.id == config['rankRole']:
                rankRole = r
            if r.id == config['editorRole']:
                editorRole = r
            if r.id == config['modRole']:
                modRole = r
            if r.id == config['adminRole']:
                adminRole = r
            if r.id == config['leaderRole']:
                leaderRole = r
        for m in members:
            roles = m.roles[1:] #get all except first role, because first role is always @everyone
            name = m.nick
            if not name:
                name = m.name
            if m.top_role >= leaderRole:
                await self.bot.say(f'Sorry, I do not have sufficient permissions to demote **{name}**.')
            elif m.top_role >= adminRole:
                if isLeader:
                    await self.bot.remove_roles(m, adminRole)
                    txt += f'**{name}** has been demoted to **Moderator**.\n'
                else:
                    await self.bot.say(f'Sorry, you need Leader permissions to demote **{name}** to **Moderator**.')
            elif m.top_role >= modRole:
                roles.remove(modRole)
                await self.bot.replace_roles(m, *roles)
                txt += f'**{name}** has been demoted to **Editor**.\n'
            elif m.top_role >= rankRole:
                roles.remove(rankRole)
                roles.remove(editorRole)
                await self.bot.replace_roles(m, *roles)
                txt += f'**{name}** has been demoted to **Smiley**.\n'
            elif m.top_role >= smileyRole:
                if vetRole in roles:
                    await self.bot.remove_roles(m, smileyRole, vetRole)
                else:
                    await self.bot.remove_roles(m, smileyRole)
                txt += f'**{name}** has been deranked.\n'
            else:
                await self.bot.say(f'**{name}** cannot be demoted any further.')
        if txt:
            await self.bot.say(txt)
        return

    @commands.command(pass_context=True)
    async def derank(self, ctx, *memberNames):
        '''
        Deranks the given user(s) (Admin+).
        '''
        addCommand()
        msg = ctx.message
        user = msg.author
        roles = user.roles
        channel = msg.channel
        server = msg.server
        isAdmin = False
        for r in roles:
            if r.id == config['adminRole'] or user.id == config['owner']:
                isAdmin = True
                break
        if not isAdmin:
            await self.bot.say('Sorry, this command can only be used by Admins and above.')
            return
        if len(msg.mentions) < 1 and not memberNames:
            await self.bot.say('Please mention the user(s) who you want to derank.')
            return
        members = msg.mentions
        if not members:
            if memberNames:
                for memberName in memberNames:
                    memberName = pattern.sub('', memberName).upper()
                    member = discord.utils.find(lambda m: isName(memberName, m), server.members)
                    if not member:
                        await self.bot.say(f'Sorry, I could not find a user by the name **{memberName}**.')
                        continue
                    members.append(member)
        isLeader = False
        for r in roles:
            if r.id == config['leaderRole'] or user.id == config['owner']:
                isLeader = True
                break
        txt = ""
        for r in server.roles:
            if r.id == config['smileyRole']:
                smileyRole = r
            if r.id == config['vetRole']:
                vetRole = r
            if r.id == config['rankRole']:
                rankRole = r
            if r.id == config['editorRole']:
                editorRole = r
            if r.id == config['modRole']:
                modRole = r
            if r.id == config['adminRole']:
                adminRole = r
            if r.id == config['leaderRole']:
                leaderRole = r
        for m in members:
            roles = m.roles[1:] #get all except first role, because first role is always @everyone
            name = m.nick
            if not name:
                name = m.name
            if m.top_role >= leaderRole:
                await self.bot.say(f'Sorry, I do not have sufficient permissions to derank **{name}**.')
            elif m.top_role >= adminRole:
                if isLeader:
                    roles.remove(adminRole)
                    roles.remove(modRole)
                    roles.remove(editorRole)
                    roles.remove(rankRole)
                    await self.bot.replace_roles(m, *roles)
                    txt += f'{name} has been deranked.\n'
                else:
                    await self.bot.say(f'Sorry, you need Leader permissions to derank **{name}**.')
            elif m.top_role >= modRole:
                roles.remove(modRole)
                roles.remove(editorRole)
                roles.remove(rankRole)
                await self.bot.replace_roles(m, *roles)
                txt += f'**{name}** has been deranked.\n'
            elif m.top_role >= rankRole:
                roles.remove(editorRole)
                roles.remove(rankRole)
                await self.bot.replace_roles(m, *roles)
                txt += f'**{name}** has been deranked.\n'
            elif m.top_role >= smileyRole:
                if vetRole in roles:
                    roles.remove(vetRole)
                roles.remove(smileyRole)
                await self.bot.replace_roles(m, *roles)
                txt += f'**{name}** has been deranked.\n'
            else:
                await self.bot.say(f'**{name}** cannot be deranked any further.')
        if txt:
            await self.bot.say(txt)
        return

    @commands.command(pass_context=True)
    async def mentionable(self, ctx, roleName=""):
        '''
        Toggles mentionable for the given role (Admin+).
        '''
        addCommand()
        msg = ctx.message
        user = msg.author
        roles = user.roles
        channel = msg.channel
        server = msg.server
        isAdmin = False
        for r in roles:
            if r.id == config['adminRole'] or user.id == config['owner']:
                isAdmin = True
                break
        if not isAdmin:
            await self.bot.say('Sorry, this command can only be used by Admins and above.')
            return
        if not roleName:
            await self.bot.say(f'Please add a valid role as an argument, such as: `{prefix[0]}mentionable rank`.')
            return
        role = ""
        for r in server.roles:
            if r.name.upper() == roleName.upper():
                role = r
                break
        if not role:
            await self.bot.say(f'Sorry, I could not find the role **{roleName}**, please check that it is a valid role.')
            return
        else:
            mentionable = role.mentionable
            emoji = ""
            x = ""
            if mentionable:
                mentionable = False
                emoji = ":no_entry_sign: "
                x = "not "
            else:
                emoji = ":white_check_mark: "
                mentionable = True
            try:
                await self.bot.edit_role(server, role, mentionable=mentionable)
                await self.bot.say(f'{emoji}Role **{roleName}** has been made **{x}mentionable**.')
                return
            except discord.Forbidden:
                await self.bot.say(f'Sorry, I do not have permission to edit the role **{roleName}**.')

    @commands.command(pass_context=True)
    async def accept(self, ctx):
        '''
        Accepts a smiley application (Admin+).
        '''
        addCommand()
        portables = self.server
        msg = ctx.message
        author = msg.author
        roles = author.roles
        server = msg.server
        channel = msg.channel
        appChannel = self.bot.get_channel(config['applicationChannel'])
        appChannelID = config['applicationChannel']
        if server != portables:
            await self.bot.say('Sorry, this command can only be used in the Portables server.')
            return
        if channel != appChannel:
            await self.bot.say(f'Sorry, this command can only be used in the <#{appChannelID}> channel.')
            return
        isAdmin = False
        for r in roles:
            if r.id == config['adminRole'] or author.id == config['owner']:
                isAdmin = True
                break
        if not isAdmin:
            await self.bot.say('Sorry, this command can only be executed by Admins and above.')
            return
        if len(msg.mentions) != 1:
            await self.bot.say('Please mention the user who you want to accept. You can only mention one at a time.')
            return
        user = msg.mentions[0]
        role = discord.utils.get(msg.server.roles, name='Smiley')
        if role in user.roles:
            await self.bot.say('Sorry, this user is already smilied.')
            return
        smileyChannelID = config['smileyChannel']
        txt = f'Congratulations {user.mention}, \n\nYour application has been **accepted**. :white_check_mark: \nIf you have any questions, please do not hesitate to DM an admin or leader, or ask for help in <#{smileyChannelID}>. \n\nThank you for the help and welcome to the team! :slight_smile:'
        await self.bot.say(txt)
        await self.bot.add_roles(user, role)
        await self.bot.delete_message(msg)
        adminChannel = self.bot.get_channel(config['adminChannel'])
        name = user.name
        if user.nick:
            name = user.nick
        await self.bot.send_message(adminChannel, f'**{author.name}** has accepted **{name}**\'s smiley application.')
        return

    @commands.command(pass_context=True)
    async def decline(self, ctx):
        '''
        Declines a smiley application (Admin+).
        '''
        addCommand()
        portables = self.server
        msg = ctx.message
        author = msg.author
        roles = author.roles
        server = msg.server
        channel = msg.channel
        appChannel = self.bot.get_channel(config['applicationChannel'])
        appChannelID = config['applicationChannel']
        if server != portables:
            await self.bot.say('Sorry, this command can only be used in the Portables server.')
            return
        if channel != appChannel:
            await self.bot.say(f'Sorry, this command can only be used in the <#{appChannelID}> channel.')
            return
        isAdmin = False
        for r in roles:
            if r.id == config['adminRole'] or author.id == config['owner']:
                isAdmin = True
                break
        if not isAdmin:
            await self.bot.say('Sorry, this command can only be executed by Admins and above.')
            return
        if len(msg.mentions) != 1:
            await self.bot.say('Please mention the user who you want to decline. You can only mention one at a time.')
            return
        user = msg.mentions[0]
        txt = f'Hi {user.mention}, \n\nUnfortunately, your application has been **declined**. :no_entry_sign: \nIf you have any questions, please do not hesitate to DM an admin or leader.'
        await self.bot.say(txt)
        await self.bot.delete_message(msg)
        adminChannel = self.bot.get_channel(config['adminChannel'])
        name = user.name
        if user.nick:
            name = user.nick
        await self.bot.send_message(adminChannel, f'**{author.name}** has declined **{name}**\'s smiley application.')
        return

    @commands.command(pass_context=True)
    async def rolecolour(self, ctx, roleName="", colour=""):
        '''
        Changes the colour of the given role to the given colour (Admin+).
        '''
        addCommand()
        if not roleName or not colour:
            msg = f'Please provide a role name and colour as parameters: `{prefix[0]}rolecolour [roleName] [#colour]`.'
            await self.bot.say(msg)
            return
        msg = ctx.message
        server = msg.server
        roles = server.roles
        roleExists = False
        role = False
        for r in roles:
            if r.name.upper() == roleName.upper():
                role = r
                roleExists = True
                break
        if not roleExists:
            await self.bot.say('Sorry, I cannot find the role **' + roleName + '**.')
            return
        match = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', colour)
        if not match:
            await self.bot.say('Sorry, **' + colour + '** is not a valid colour.')
            return
        colour = colour.replace("#", "0x")
        colour = int(colour, 16)
        colour = discord.Colour(colour)
        user = msg.author
        roles = user.roles
        isAdmin = False
        for r in roles:
            if r.id == config['adminRole'] or user.id == config['owner']:
                isAdmin = True
                break
        if not isAdmin:
            await self.bot.say('Sorry, this command can only be executed by Admins and above.')
            return
        try:
            await self.bot.edit_role(server, role, colour=colour)
            await self.bot.say('The colour for role **' + role.name + '** has been changed to **' + str(colour) + '**.')
        except discord.Forbidden:
            await self.bot.say('Sorry, I do not have permission to change the colour of role **' + role.name + '**.')

def setup(bot):
    bot.add_cog(ModCommands(bot))
