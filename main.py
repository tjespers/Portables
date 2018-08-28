import asyncio
from datetime import datetime, timedelta, timezone
import json
import logging
from pathlib import Path
import tweepy
import subprocess
from subprocess import call
from sys import exit
import os
from random import randint
import html
import re
import discord
from discord.ext import commands
import codecs
import multiprocessing
import sys

pattern = re.compile('([^\s\w]|_)+')

prefix = ['-']

loggingBool = True

commandsAnswered = 0

def addCommand():
    global commandsAnswered
    commandsAnswered += 1

def getCommandsAnswered():
    return commandsAnswered

def toggleLogging():
    global loggingBool
    if loggingBool:
        loggingBool = False
    else:
        loggingBool = True

def isLogging():
    return loggingBool

def config_load():
    with codecs.open('data/config.json', 'r', encoding='utf-8-sig') as doc:
        #  Please make sure encoding is correct, especially after editing the config file
        return json.load(doc)

def restart():
    print("Restarting script...")
    '''
    dir = os.path.dirname(os.path.realpath(__file__))
    cmdline = "Portables.bat"
    call("start cmd /K " + cmdline, cwd=dir, shell=True)
    print("New script started, quitting...")
    '''
    exit(0)

def timeDiffToString(time):
    seconds = time.seconds
    days = time.days
    hours = seconds // 3600
    seconds -= hours * 3600
    minutes = seconds // 60
    seconds -= minutes * 60
    time = ""
    if days != 0:
        time += str(days) + " day"
        if days != 1:
            time += "s"
    if hours != 0:
        if days != 0:
            time += ", "
            if minutes == 0 and seconds == 0:
                time += "and "
        time += str(hours) + " hour"
        if hours != 1:
            time += "s"
    if minutes != 0:
        if days != 0 or hours != 0:
            time += ", "
            if seconds == 0:
                time += "and "
        time += str(minutes) + " minute"
        if minutes != 1:
            time += "s"
    if seconds != 0:
        if days != 0 or hours != 0 or minutes != 0:
            time += ", and "
        time += str(seconds) + " second"
        if seconds != 1:
            time += "s"
    return time

async def run():
    """
    Where the bot gets started. If you wanted to create a database connection pool or other session for the bot to use,
    it's recommended that you create it here and pass it to the bot as a kwarg.
    """
    config = config_load()
    bot = Bot(config=config,
              description=config['description'])
    try:
        await bot.start(config['token'])
    except KeyboardInterrupt:
        await bot.logout()

class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            max_messages = 100000,
            command_prefix=self.get_prefix_,
            description=kwargs.pop('description')
        )
        self.start_time = None
        self.app_info = None
        self.loop.create_task(self.track_start())

    async def track_start(self):
        """
        Waits for the bot to connect to discord and then records the time.
        Can be used to work out uptime.
        """
        await self.wait_until_ready()
        self.start_time = datetime.utcnow()

    async def get_prefix_(self, bot, message):
        """
        A coroutine that returns a prefix.

        I have made this a coroutine just to show that it can be done. If you needed async logic in here it can be done.
        A good example of async logic would be retrieving a prefix from a database.
        """
        return commands.when_mentioned_or(*prefix)(bot, message)

    async def load_all_extensions(self):
        """
        Attempts to load all .py files in /cogs/ as cog extensions
        """
        await self.wait_until_ready()
        config = config_load()
        channel = self.get_channel(config['logsChannel'])
        cogs = [x.stem for x in Path('cogs').glob('*.py')]
        msg = ""
        for extension in cogs:
            try:
                self.load_extension(f'cogs.{extension}')
                print(f'Loaded extension: {extension}')
                msg += f'Loaded extension: {extension}\n'
            except Exception as e:
                error = f'{extension}\n {type(e).__name__} : {e}'
                print(f'Failed to load extension: {error}')
                msg += f'Failed to load extension: {error}\n'
        print('-' * 10)
        logging.info(msg)
        if 'Failed' in msg:
            await self.send_message(channel, msg)
        else:
            await self.send_message(channel, f'Succesfully loaded all extensions')

    async def on_ready(self):
        """
        This event is called every time the bot connects or resumes connection.
        """
        config = config_load()
        await self.change_presence(game=discord.Game(type=0, name=f'#notifications | {prefix[0]}help'))
        channel = self.get_channel(config['logsChannel'])
        print('-' * 10)
        self.app_info = await self.application_info()
        msg = (f'Logged in to Discord as: {self.user.name}\n'
               f'Using discord.py version: {discord.__version__}\n'
               f'Owner: {self.app_info.owner}\n'
               f'Time: {str(self.start_time)} UTC')
        print(msg)
        print('-' * 10)
        discord_msg = msg
        logging.info(msg)
        auth = tweepy.OAuthHandler(config['consumer_key'], config['consumer_secret'])
        auth.set_access_token(config['access_token_key'], config['access_token_secret'])
        api = tweepy.API(auth)
        me = api.me().screen_name
        msg = (f'Logged in to Twitter as: {me}\n'
               f'Using tweepy version: {tweepy.__version__}')
        print(msg)
        print('-' * 10)
        discord_msg += '\n' + msg
        logging.info(msg)
        for chan in self.get_server(config['portablesServer']).channels:
            async for m in self.logs_from(chan):
                self.messages.append(m)
        msg = f'Loaded old messages'
        print(msg)
        print('-' * 10)
        discord_msg += '\n' + msg
        logging.info(msg)
        await self.send_message(channel, discord_msg)
        self.loop.create_task(self.load_all_extensions())
        self.loop.create_task(self.role_setup())
        self.loop.create_task(self.notify(api))

    async def role_setup(self):
        config = config_load()
        channel = self.get_channel(config['roleChannel'])
        emojis = [config['warbandsEmoji'], config['amloddEmoji'], config['hefinEmoji'], config['ithellEmoji'],
                  config['trahaearnEmoji'], config['meilyrEmoji'], config['crwysEmoji'], config['cadarnEmoji'],
                  config['iorwerthEmoji'], config['cacheEmoji'], config['sinkholeEmoji'], config['yewsEmoji'],
                  config['goebiesEmoji'], config['merchantEmoji'], config['happyHourEmoji']]
        messages = 0
        async for message in self.logs_from(channel, limit=1):
            self.messages.append(message)
            messages += 1
        if not messages:
            msg = "React to this message with any of the following emoji to be added to the corresponding role for notifications:\n\n"
            msg += config['amloddEmoji'] + " Amlodd\n"
            msg += config['hefinEmoji'] + " Hefin\n"
            msg += config['ithellEmoji'] + " Ithell\n"
            msg += config['trahaearnEmoji'] + " Trahaearn\n"
            msg += config['meilyrEmoji'] + " Meilyr\n"
            msg += config['crwysEmoji'] + " Crwys\n"
            msg += config['cadarnEmoji'] + " Cadarn\n"
            msg += config['iorwerthEmoji'] + " Iorwerth\n"
            msg += config['cacheEmoji'] + " Caches\n"
            msg += config['sinkholeEmoji'] + " Sinkholes\n"
            msg += config['yewsEmoji'] + " Yews\n"
            msg += config['goebiesEmoji'] + " Goebies\n"
            msg += config['warbandsEmoji'] + " Warbands\n"
            msg += config['merchantEmoji'] + " Merchant\n"
            msg += config['happyHourEmoji'] + " Happy Hour\n"
            msg += "\nIf you wish to stop receiving notifications, simply remove your reaction. If your reaction isn't there anymore, then you can add a new one and remove it."
            await self.send_message(channel, msg)
            async for message in self.logs_from(channel, limit=1):
                serverEmojis = self.get_all_emojis()
                emojiNames = []
                for emoji in emojis:
                    emoji = emoji[emoji.find(":")+1:len(emoji)-1]
                    emoji = emoji[0:emoji.find(":")]
                    emojiNames.append(emoji)
                for e in serverEmojis:
                    for emoji in emojiNames:
                        if e.name == emoji:
                            await self.add_reaction(message, e)
                            break
        msg = f'Now managing roles in <#{channel.id}> on server {channel.server.name}'
        print(msg)
        print('-' * 10)
        logChannel = self.get_channel(config['logsChannel'])
        logging.info(msg)
        await self.send_message(logChannel, msg)


    async def on_member_join(self, member):
        config = config_load()
        server = member.server
        portables = self.get_server(config['portablesServer'])
        if server != portables:
            return
        channel = self.get_channel(config['welcomeChannel'])
        logsChannel = self.get_channel(config['logsChannel'])
        if "DISCORD.GG" in member.name.upper() or "ADD ME" in member.name.upper() or "ADDME" in member.name.upper() or (member.name == "GamingHD" and member.discriminator == "8723"):
            await self.bot.ban(member)
            msg = f'I have banned **{member.name}** upon joining.'
            await self.send_message(logsChannel, msg)
        else:
            msg = f'Welcome to **{server.name}**, {member.mention}!'
            await self.send_message(channel, msg)

    async def on_reaction_add(self, reaction, user):
        config = config_load()
        msg = reaction.message
        channel = msg.channel
        if user.bot:
            return
        if channel.id == config['roleChannel']:
            emoji = reaction.emoji
            roleName = emoji.name
            if emoji.name in ["Warbands", "Amlodd", "Hefin", "Ithell", "Trahaearn", "Meilyr", "Crwys", "Cadarn", "Iorwerth", "Cache", "Sinkhole", "Yews", "Goebies", "Merchant", "HappyHour"]:
                role = discord.utils.get(user.server.roles, name=roleName)
                await self.add_roles(user, role)
                addCommand()

    async def on_reaction_remove(self, reaction, user):
        config = config_load()
        msg = reaction.message
        channel = msg.channel
        if channel.id != config['roleChannel'] or user.bot:
            return
        emoji = reaction.emoji
        roleName = emoji.name
        if emoji.name in ["Warbands", "Amlodd", "Hefin", "Ithell", "Trahaearn", "Meilyr", "Crwys", "Cadarn", "Iorwerth", "Cache", "Sinkhole", "Yews", "Goebies", "Merchant", "HappyHour"]:
            role = discord.utils.get(user.server.roles, name=roleName)
            await self.remove_roles(user, role)
            addCommand()

    async def on_message(self, message):
        """
        This event triggers on every message received by the bot. Including one's that it sent itself.

        If you wish to have multiple event listeners they can be added in other cogs. All on_message listeners should
        always ignore bots.
        """
        if message.author.bot:
            return  # ignore all bots
        await self.process_commands(message)

    async def notify(self, api):
        config = config_load()
        try:
            channel = self.get_channel(config['notificationChannel'])
            notifiedThisHourWarbands = False
            notifiedThisHourVOS = False
            notifiedThisHourCache = False
            notifiedThisHourYews48 = False
            notifiedThisHourYews140 = False
            notifiedThisHourGoebies = False
            notifiedThisHourSinkhole = False
            notifiedThisDayMerchant = False
            notifiedThisHourHappyHour = False
            reset = False
            currentTime = datetime.utcnow()
            async for m in self.logs_from(channel, limit=20):
                if m.timestamp.day == currentTime.day:
                    if 'Merchant' in m.content:
                        notifiedThisDayMerchant = True
                        break
                    if m.timestamp.hour == currentTime.hour:
                        if any(district in m.content for district in ["Amlodd", "Hefin", "Ithell", "Trahaearn", "Meilyr", "Crwys", "Cadarn", "Iorwerth"]):
                            notifiedThisHourVOS = True
                            break
                        if 'Cache' in m.content:
                            notifiedThisHourCache = True
                            break
                        if 'yew' in m.content:
                            if '48' in m.content:
                                notifiedThisHourYews48 = True
                            elif '140' in m.content:
                                notifiedThisHourYews140 = True
                            break
                        if 'Goebies' in m.content:
                            notifiedThisHourGoebies = True
                            break
                        if 'Sinkhole' in m.content:
                            notifiedThisHourSinkhole = True
                            break
                        if 'Happy' in m.content:
                            notifiedThisHourHappyHour = True
                            break
            msg = f'Now sending notifications in <#{channel.id}> on server {channel.server.name}'
            logging.info(msg)
            print(msg)
            print('-' * 10)
            logChannel = self.get_channel(config['logsChannel'])
            await self.send_message(logChannel, msg)
            i = 0
            while True:
                now = datetime.utcnow()
                i += 1
                i %= 30
                if not notifiedThisDayMerchant and i == 1:
                    merchantTweets = api.user_timeline(screen_name="Travellingmerc1", count=1, tweet_mode="extended")
                    for tweet in merchantTweets:
                        tweetTime = tweet.created_at
                        if now.day != tweetTime.day or now.hour != tweetTime.hour:
                            continue
                        if '(, )' in html.unescape(tweet.full_text):
                            break
                        await self.send_message(channel, config['msgMerchant'] + config['merchantRole'] + "\n" + html.unescape(tweet.full_text))
                        notifiedThisDayMerchant = True
                if not notifiedThisHourVOS and now.minute <= 1:
                    jagexTweets = api.user_timeline(screen_name="JagexClock", count=5)
                    msg = ""
                    for tweet in jagexTweets:
                        tweetTime = tweet.created_at
                        if now.hour != tweetTime.hour or not "Voice of Seren" in tweet.text:
                            continue
                        if "Amlodd" in tweet.text:
                            msg += config['msgAmlodd'] + config['AmloddRole'] + '\n'
                        if "Hefin" in tweet.text:
                            msg += config['msgHefin'] + config['HefinRole'] + '\n'
                        if "Ithell" in tweet.text:
                            msg += config['msgIthell'] + config['ithellRole'] + '\n'
                        if "Trah" in tweet.text:
                            msg += config['msgTrahaearn'] + config['TrahaearnRole'] + '\n'
                        if "Meilyr" in tweet.text:
                            msg += config['msgMeilyr'] + config['meilyrRole'] + '\n'
                        if "Crwys" in tweet.text:
                            msg += config['msgCrwys'] + config['crwysRole'] + '\n'
                        if "Cadarn" in tweet.text:
                            msg += config['msgCadarn'] + config['cadarnRole'] + '\n'
                        if "Iorwerth" in tweet.text:
                            msg += config['msgIorwerth'] + config['iorwerthRole'] + '\n'
                        if msg:
                            notifiedThisHourVOS = True
                            await self.send_message(channel, msg)
                            break
                if not notifiedThisHourWarbands and now.minute >= 45 and now.minute <= 46:
                    jagexTweets = api.user_timeline(screen_name="JagexClock", count=5)
                    for tweet in jagexTweets:
                        tweetTime = tweet.created_at
                        if now.day != tweetTime.day or now.hour != tweetTime.hour:
                            continue
                        if "Warbands" in tweet.text:
                            await self.send_message(channel, config['msgWarbands'] + config['warbandsRole'])
                            notifiedThisHourWarbands = True
                            break
                if not notifiedThisHourCache and now.minute >= 55 and now.minute <= 56:
                    await self.send_message(channel, config['msgCache'] + config['cacheRole'])
                    notifiedThisHourCache = True
                if not notifiedThisHourYews48 and now.hour == 23 and now.minute >= 45 and now.minute <= 46:
                    await self.send_message(channel, config['msgYews48'] + config['yewsRole'])
                    notifiedThisHourYews48 = True
                if not notifiedThisHourYews140 and now.hour == 17 and now.minute >= 45 and now.minute <= 46:
                    await self.send_message(channel, config['msgYews140'] + config['yewsRole'])
                    notifiedThisHourYews140 = True
                if not notifiedThisHourGoebies and now.hour in [11, 23] and now.minute >= 45 and now.minute <= 46:
                    await self.send_message(channel, config['msgGoebies'] + config['goebiesRole'])
                    notifiedThisHourGoebies = True
                if not notifiedThisHourSinkhole and now.minute >= 25 and now.minute <= 26:
                    await self.send_message(channel, config['msgSinkhole'] + config['sinkholeRole'])
                    notifiedThisHourSinkhole = True
                if not notifiedThisHourHappyHour and ((now.hour in [0, 8, 13, 20] and now.minute >= 45 and now.minute <= 46) or (now.hour == 16 and now.minute >= 15 and now.minute <= 16)):
                    await self.send_message(channel, config['msgHappyHour'] + config['happyHourRole'])
                    notifiedThisHourHappyHour = True

                if now.minute > 1 and reset:
                    reset = False
                if now.minute == 0 and not reset:
                    notifiedThisHourWarbands = False
                    notifiedThisHourVOS = False
                    notifiedThisHourCache = False
                    notifiedThisHourYews48 = False
                    notifiedThisHourYews140 = False
                    notifiedThisHourGoebies = False
                    notifiedThisHourSinkhole = False
                    notifiedThisHourHappyHour = False
                    if now.hour == 0:
                        notifiedThisDayMerchant = False
                    reset = True
                await asyncio.sleep(10)
        except Exception as e:
            error = f'Encountered the following error in notification loop:\n{type(e).__name__} : {e}\nRestarting...'
            logging.critical(error)
            print(error)
            channel = self.get_channel(config['logsChannel'])
            await self.send_message(channel, error)
            restart()



if __name__ == '__main__':
    logging.basicConfig(filename='data/log.txt', level=logging.INFO)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
