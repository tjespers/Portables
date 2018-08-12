import asyncio
import discord
from discord.ext import commands
from main import config_load
from main import prefix
from main import isLogging
from datetime import datetime, timedelta, timezone

config = config_load()

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

deleteCount = 0

testCounter = 0

def addDelete():
    global deleteCount
    deleteCount += 1

def getDeleteCount():
    return deleteCount

def resetDeleteCount():
    global deleteCount
    deleteCount = 0

eventsLogged = 0

def logEvent():
    global eventsLogged
    eventsLogged += 1

def getEventsLogged():
    return eventsLogged

class Logs:
    def __init__(self, bot):
        self.bot = bot
        self.channel = bot.get_channel(config['logsChannel'])
        self.start_time = datetime.utcnow()
        self.server = bot.get_server(config['portablesServer'])

    async def on_member_join(self, member):
        if member.server != self.server:
            return
        if isLogging():
            logEvent()
            title = f'**Member Joined**'
            colour = 0x00e400
            timestamp = datetime.utcnow()
            id = f'User ID: {member.id}'
            creationTime = member.created_at
            time = f'{creationTime.day} {months[creationTime.month-1]} {creationTime.year}, {creationTime.hour}:{creationTime.minute}'
            txt = (f'{member.mention} {member.name}#{member.discriminator}\n'
                   f'Account creation: {time}')
            url = member.avatar_url
            embed = discord.Embed(title=title, colour=colour, timestamp=timestamp, description=txt)
            embed.set_footer(text=id)
            embed.set_thumbnail(url=url)
            await self.bot.send_message(self.channel, embed=embed)
            return

    async def on_member_remove(self, member):
        if member.server != self.server:
            return
        if isLogging():
            banlist = await self.bot.get_bans(self.server)
            for user in banlist:
                if user == member:
                    return
            logEvent()
            title = f'**Member Left**'
            colour = 0xff0000
            timestamp = datetime.utcnow()
            id = f'User ID: {member.id}'
            txt = f'{member.mention} {member.name}#{member.discriminator}'
            url = member.avatar_url
            embed = discord.Embed(title=title, colour=colour, timestamp=timestamp, description=txt)
            embed.set_footer(text=id)
            embed.set_thumbnail(url=url)
            await self.bot.send_message(self.channel, embed=embed)
            return

    async def on_member_ban(self, member):
        if member.server != self.server:
            return
        if isLogging():
            logEvent()
            title = f'**Member Banned**'
            colour = 0xff0000
            timestamp = datetime.utcnow()
            id = f'User ID: {member.id}'
            txt = f'{member.mention} {member.name}#{member.discriminator}'
            url = member.avatar_url
            embed = discord.Embed(title=title, colour=colour, timestamp=timestamp, description=txt)
            embed.set_footer(text=id)
            embed.set_thumbnail(url=url)
            await self.bot.send_message(self.channel, embed=embed)
            return

    async def on_member_unban(self, server, user):
        if server != self.server:
            return
        if isLogging():
            logEvent()
            title = f'**Member Unbanned**'
            colour = 0xff7b1f
            timestamp = datetime.utcnow()
            id = f'User ID: {user.id}'
            txt = f'{user.name}#{user.discriminator}'
            url = user.avatar_url
            embed = discord.Embed(title=title, colour=colour, timestamp=timestamp, description=txt)
            embed.set_footer(text=id)
            embed.set_thumbnail(url=url)
            await self.bot.send_message(self.channel, embed=embed)
            return

    async def on_message_delete(self, message):
        if message.server != self.server:
            return
        if isLogging():
            global testCounter
            testCounter += 1
            i = testCounter
            bulk = 0
            addDelete()
            count = getDeleteCount()
            await asyncio.sleep(1)
            newCount = getDeleteCount()
            if newCount > count:
                bulk = 0
            elif newCount == 1:
                bulk = 1
            else:
                bulk = newCount
            if count >= newCount:
                resetDeleteCount()
            if message.embeds and bulk == 1 or bulk == 0:
                return
            if bulk > 1:
                logEvent()
                title = f'**Bulk Delete**'
                colour = 0x00b2ff
                timestamp = datetime.utcnow()
                txt = f'{bulk} messages deleted in {message.channel.mention}'
                embed = discord.Embed(title=title, colour=colour, timestamp=timestamp, description=txt)
                await self.bot.send_message(self.channel, embed=embed)
                return
            logEvent()
            member = message.author
            title = f'**Message Deleted**'
            colour = 0x00b2ff
            timestamp = datetime.utcnow()
            id = f'Message ID: {message.id}'
            txt = (f'By: {member.mention} {member.name}#{member.discriminator}\n'
                   f'In: {message.channel.mention}')
            url = member.avatar_url
            embed = discord.Embed(title=title, colour=colour, timestamp=timestamp, description=txt)
            msg = message.content
            if len(msg) > 1000:
                msg = msg[:1000] + '\n...'
            embed.add_field(name='Message', value=message.content, inline=False)
            embed.set_footer(text=id)
            embed.set_thumbnail(url=url)
            await self.bot.send_message(self.channel, embed=embed)
            return

    async def on_message_edit(self, before, after):
        if isLogging():
            member = after.author
            if member.bot or before.embeds or after.embeds:
                return
            if after.server != self.server:
                return
            logEvent()
            title = f'**Message Edited**'
            colour = 0x00b2ff
            timestamp = datetime.utcnow()
            id = f'Message ID: {after.id}'
            txt = (f'By: {member.mention} {member.name}#{member.discriminator}\n'
                   f'In: {after.channel.mention}')
            url = member.avatar_url
            beforeContent = before.content
            if not beforeContent:
                beforeContent = 'N/A'
            afterContent = after.content
            if not afterContent:
                afterContent = 'N/A'
            if len(beforeContent) > 1000:
                beforeContent = beforeContent[:1000] + '\n...'
            if len(afterContent) > 1000:
                afterContent = afterContent[:1000] + '\n...'
            embed = discord.Embed(title=title, colour=colour, timestamp=timestamp, description=txt)
            embed.add_field(name='Before', value=beforeContent, inline=False)
            embed.add_field(name='After', value=afterContent, inline=False)
            embed.set_footer(text=id)
            embed.set_thumbnail(url=url)
            await self.bot.send_message(self.channel, embed=embed)
            return

    async def on_channel_delete(self, channel):
        if channel.server != self.server:
            return
        if isLogging():
            logEvent()
            title = f'**Channel Deleted**'
            colour = 0xff0000
            timestamp = datetime.utcnow()
            id = f'Channel ID: {channel.id}'
            creationTime = channel.created_at
            time = f'{creationTime.day} {months[creationTime.month-1]} {creationTime.year}, {creationTime.hour}:{creationTime.minute}'
            txt = (f'**{channel.name}** was deleted\n'
                   f'Channel creation: {time}.')
            embed = discord.Embed(title=title, colour=colour, timestamp=timestamp, description=txt)
            embed.set_footer(text=id)
            await self.bot.send_message(self.channel, embed=embed)
            return

    async def on_channel_create(self, channel):
        if channel.server != self.server:
            return
        if isLogging():
            logEvent()
            title = f'**Channel Created**'
            colour = 0x00e400
            timestamp = datetime.utcnow()
            id = f'Channel ID: {channel.id}'
            txt = f'{channel.mention}'
            embed = discord.Embed(title=title, colour=colour, timestamp=timestamp, description=txt)
            embed.set_footer(text=id)
            await self.bot.send_message(self.channel, embed=embed)
            return

    async def on_member_update(self, before, after):
        if before.server != self.server:
            return
        if before.nick != after.nick and isLogging():
            logEvent()
            title = f'**Nickname Changed**'
            colour = 0x00b2ff
            timestamp = datetime.utcnow()
            id = f'User ID: {after.id}'
            txt = f'{after.mention} {after.name}#{after.discriminator}'
            url = after.avatar_url
            embed = discord.Embed(title=title, colour=colour, timestamp=timestamp, description=txt)
            beforeNick = before.nick
            if not beforeNick:
                beforeNick = 'N/A'
            afterNick = after.nick
            if not afterNick:
                afterNick = 'N/A'
            embed.add_field(name='Before', value=beforeNick, inline=False)
            embed.add_field(name='After', value=afterNick, inline=False)
            embed.set_footer(text=id)
            embed.set_thumbnail(url=url)
            await self.bot.send_message(self.channel, embed=embed)
            return
        elif before.roles != after.roles:
            addedRoles = []
            removedRoles = []
            for r in before.roles:
                if not r in after.roles:
                    removedRoles.append(r)
            for r in after.roles:
                if not r in before.roles:
                    addedRoles.append(r)
            title = f'**Roles Changed**'
            colour = 0x00b2ff
            timestamp = datetime.utcnow()
            id = f'User ID: {after.id}'
            txt = f'{after.mention} {after.name}#{after.discriminator}'
            url = after.avatar_url
            embed = discord.Embed(title=title, colour=colour, timestamp=timestamp, description=txt)
            added = ""
            if addedRoles:
                count = 0
                for role in addedRoles:
                    count += 1
                    added += role.name
                    if count < len(addedRoles):
                        added += ", "
                embed.add_field(name='Added', value=added, inline=False)
            removed = ""
            if removedRoles:
                count = 0
                for role in removedRoles:
                    count += 1
                    removed += role.name
                    if count < len(removedRoles):
                        removed += ", "
                embed.add_field(name='Removed', value=removed, inline=False)
            embed.set_footer(text=id)
            embed.set_thumbnail(url=url)
            for r in self.server.roles:
                if r.id == config['rankRole']:
                    rankRole = r
            if isLogging():
                logEvent()
                await self.bot.send_message(self.channel, embed=embed)
            if 'Smiley' in added and not 'Rank' in removed and not rankRole in before.roles:
                smileyChannel = self.bot.get_channel(config['smileyChannel'])
                locChannel = self.bot.get_channel(config['locChannel'])
                msg = (f'Welcome to {smileyChannel.mention}, {after.mention}!\n'
                       f'Please use this channel for any FC related discussions, questions, and issues.\n\n'
                       f'Please check the pinned messages in this channel and in {locChannel.mention}, where you’ll be able to edit our sheets by updating locations, for important posts and details.')
                await self.bot.send_message(smileyChannel, msg)
            elif 'Rank' in added:
                rankChannel = self.bot.get_channel(config['rankChannel'])
                msg = (f'Welcome {after.mention}, and congratulations on your rank!\n'
                       f'If you have any questions, feel free to ask for help here in {rankChannel.mention}, or DM an Admin+.')
                await self.bot.send_message(rankChannel, msg)
            elif 'Moderator' in added and not 'Admin' in removed:
                modChannel = self.bot.get_channel(config['modChannel'])
                msg = (f'Welcome {after.mention}, and congratulations on your promotion!\n\n'
                       f'As a Moderator, you now have the ability to ban players from the FC. To do so, head over to the \'Bans\' tab on the sheets, and in a new row enter all the necessary information and set the status to \'Pending\'. Then send a message here in {modChannel.mention} along the lines of \"[player] to be banned\", and a Leader will apply the ban for you.\n\n'
                       f'If you have any questions, or if you\'re ever unsure about banning someone, feel free to discuss it here, or DM an Admin+ for advice.')
                await self.bot.send_message(modChannel, msg)
            return


    async def on_server_update(self, before, after):
        if after != self.server:
            return
        if isLogging():
            if before.name != after.name:
                logEvent()
                owner = server.owner
                title = f'**Server Name Changed**'
                colour = 0x00b2ff
                timestamp = datetime.utcnow()
                id = f'Server ID: {after.id}'
                txt = f'Owner: {owner.mention} {owner.name}#{owner.discriminator}'
                url = after.icon_url
                embed = discord.Embed(title=title, colour=colour, timestamp=timestamp, description=txt)
                beforeName = before.name
                if not beforeName:
                    beforeName = 'N/A'
                afterName = after.name
                if not afterName:
                    afterName = 'N/A'
                embed.add_field(name='Before', value=beforeName, inline=False)
                embed.add_field(name='After', value=afterName, inline=False)
                embed.set_footer(text=id)
                embed.set_thumbnail(url=url)
                await self.bot.send_message(self.channel, embed=embed)
                return

    async def on_server_role_create(self, role):
        if role.server != self.server:
            return
        if isLogging():
            logEvent()
            title = f'**Role Created**'
            colour = 0x00e400
            timestamp = datetime.utcnow()
            id = f'Role ID: {role.id}'
            txt = f'{role.mention}'
            embed = discord.Embed(title=title, colour=colour, timestamp=timestamp, description=txt)
            embed.set_footer(text=id)
            await self.bot.send_message(self.channel, embed=embed)
            return

    async def on_server_role_delete(self, role):
        if role.server != self.server:
            return
        if isLogging():
            logEvent()
            title = f'**Role Deleted**'
            colour = 0xff0000
            timestamp = datetime.utcnow()
            id = f'Role ID: {role.id}'
            txt = f'{role.name}'
            embed = discord.Embed(title=title, colour=colour, timestamp=timestamp, description=txt)
            embed.set_footer(text=id)
            await self.bot.send_message(self.channel, embed=embed)
            return

    async def on_server_role_update(self, before, after):
        if after.server != self.server:
            return
        if isLogging():
            if before.name != after.name:
                logEvent()
                title = f'**Role Name Changed**'
                colour = 0x00b2ff
                timestamp = datetime.utcnow()
                id = f'Role ID: {after.id}'
                txt = f'Role: {after.mention}'
                embed = discord.Embed(title=title, colour=colour, timestamp=timestamp, description=txt)
                embed.add_field(name='Before', value=before.name, inline=False)
                embed.add_field(name='After', value=after.name, inline=False)
                embed.set_footer(text=id)
                await self.bot.send_message(self.channel, embed=embed)
                return

    async def on_server_emojis_update(self, before, after):
        if after:
            if after[0].server != self.server:
                return
        elif before:
            if before[0].server != self.server:
                return
        if isLogging():
            logEvent()
            if len(before) > len(after):
                title = f'**Emoji Deleted**'
                colour = 0xff0000
            else:
                title = f'**Role Created**'
                colour = 0x00e400
            timestamp = datetime.utcnow()
            id = f'Server ID: {self.server.id}'
            txt = f'{len(after)} emojis'
            embed = discord.Embed(title=title, colour=colour, timestamp=timestamp, description=txt)
            embed.set_footer(text=id)
            await self.bot.send_message(self.channel, embed=embed)
            return

def setup(bot):
    bot.add_cog(Logs(bot))
