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
import tweepy
from main import addCommand
from main import timeDiffToString

config = config_load()
auth = tweepy.OAuthHandler(config['consumer_key'], config['consumer_secret'])
auth.set_access_token(config['access_token_key'], config['access_token_secret'])
api = tweepy.API(auth)

class DNDCommands:
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.utcnow()
        server = bot.get_server(config['portablesServer'])
        self.server = server

    @commands.command(pass_context=True)
    async def future(self, ctx):
        '''
        Returns the time until all future events.
        '''
        addCommand()
        now = datetime.utcnow()
        now = now.replace(microsecond=0)
        lastWarband = now
        jagexTweets = api.user_timeline(screen_name="JagexClock", count=20)
        for tweet in jagexTweets:
            tweetTime = tweet.created_at
            if "Warbands" in tweet.text:
                lastWarband = tweetTime
                lastWarband = lastWarband.replace(second=0)
                break
        timeToWarband = (timedelta(hours=7, minutes=15) - (now - lastWarband)) % timedelta(hours=7)
        timeToWarband = timeDiffToString(timeToWarband)
        timeToVos = timedelta(hours=1) - timedelta(minutes=now.minute, seconds=now.second)
        timeToVos = timeDiffToString(timeToVos)
        timeToCache = timeToVos
        timeToYews48 = timedelta(days=1) - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
        timeToYews48 = timeDiffToString(timeToYews48)
        timeToYews140 = timedelta(days=1) - timedelta(hours=((now.hour+6)%24), minutes=now.minute, seconds=now.second)
        timeToYews140 = timeDiffToString(timeToYews140)
        timeToGoebies = timedelta(hours=12) - timedelta(hours=(now.hour%12), minutes=now.minute, seconds=now.second)
        timeToGoebies = timeDiffToString(timeToGoebies)
        timeToSinkhole = timedelta(hours=1) - timedelta(minutes=((now.minute+30)%60), seconds=now.second)
        timeToSinkhole = timeDiffToString(timeToSinkhole)
        timeToMerchant = timeToYews48
        times = [1.0, 9.0, 14.0, 16.5, 21.0]
        next = 25.0
        for time in times:
            if time > (now.hour + now.minute/60):
                next = time
                break
        hour = int(next)
        minute = next % 1
        timeToHappyHour = timedelta(hours=hour, minutes=minute) - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
        timeToHappyHour = timeDiffToString(timeToHappyHour)

        msg = (f'Future:\n'
               f'{config["warbandsEmoji"]} **Wilderness warbands** will begin in {timeToWarband}.\n'
               f'{config["vosEmoji"]} **Voice of Seren** will change in {timeToVos}.\n'
               f'{config["cacheEmoji"]} **Guthixian caches** will begin in {timeToCache}.\n'
               f'{config["yewsEmoji"]} **Divine yews** (w48 bu) will begin in {timeToYews48}.\n'
               f'{config["yewsEmoji"]} **Divine yews** (w140 bu) will begin in {timeToYews140}.\n'
               f'{config["goebiesEmoji"]} **Goebies supply run** will begin in {timeToGoebies}.\n'
               f'{config["sinkholeEmoji"]} **Sinkhole** will spawn in {timeToSinkhole}.\n'
               f'{config["merchantEmoji"]} **Travelling merchant** stock will refresh in {timeToMerchant}.\n'
               f'{config["happyHourEmoji"]} **Happy Hour** will begin in {timeToHappyHour}.')
        await self.bot.say(msg)

    @commands.command(pass_context=True)
    async def vos(self, ctx):
        '''
        Returns the current Voice of Seren.
        '''
        addCommand()
        now = datetime.utcnow()
        now = now.replace(microsecond=0)
        msg = "The current **Voice of Seren** is: "
        jagexTweets = api.user_timeline(screen_name="JagexClock", count=5)
        for tweet in jagexTweets:
            if "Amlodd" in tweet.text or "Hefin" in tweet.text or "Ithell" in tweet.text or "Trah" in tweet.text or "Meilyr" in tweet.text or "Crwys" in tweet.text or "Cadarn" in tweet.text or "Iorwerth" in tweet.text:
                count = 0
                if "Amlodd" in tweet.text:
                    msg += config['amloddEmoji'] + " **Amlodd**"
                    msg += " and " if not count else "."
                    count += 1
                if "Hefin" in tweet.text:
                    msg += config['hefinEmoji'] + " **Hefin**"
                    msg += " and " if not count else "."
                    count += 1
                if "Ithell" in tweet.text:
                    msg += config['ithellEmoji'] + " **Ithell**"
                    msg += " and " if not count else "."
                    count += 1
                if "Trah" in tweet.text:
                    msg += config['trahaearnEmoji'] + " **Trahaearn**"
                    msg += " and " if not count else "."
                    count += 1
                if "Meilyr" in tweet.text:
                    msg += config['meilyrEmoji'] + " **Meilyr**"
                    msg += " and " if not count else "."
                    count += 1
                if "Crwys" in tweet.text:
                    msg += config['crwysEmoji'] + " **Crwys**"
                    msg += " and " if not count else "."
                    count += 1
                if "Cadarn" in tweet.text:
                    msg += config['cadarnEmoji'] + " **Cadarn**"
                    msg += " and " if not count else "."
                    count += 1
                if "Iorwerth" in tweet.text:
                    msg += config['iorwerthEmoji'] + " **Iorwerth**"
                    msg += " and " if not count else "."
                    count += 1
                break
        timeToVos = timedelta(hours=1) - timedelta(minutes=now.minute, seconds=now.second)
        timeToVos = timeDiffToString(timeToVos)
        msg += "\nThis will change in " + timeToVos + "."
        await self.bot.say(msg)

    @commands.command(pass_context=True)
    async def merchant(self, ctx):
        '''
        Returns the current travelling merchant stock.
        '''
        addCommand()
        now = datetime.utcnow()
        now = now.replace(microsecond=0)
        timeToMerchant = timedelta(days=1) - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
        timeToMerchant = timeDiffToString(timeToMerchant)
        merchantTweets = api.user_timeline(screen_name="Travellingmerc1", count=1, tweet_mode="extended")
        for tweet in merchantTweets:
            tweetTime = tweet.created_at
            msg = config['merchantEmoji'] + " " + html.unescape(tweet.full_text)
            msg += "\nStock will refresh soon!" if tweetTime.day != now.day else "\nStock will refresh in " + timeToMerchant + "."
            await self.bot.say(msg)

    @commands.command(pass_context=True)
    async def warbands(self, ctx):
        '''
        Returns the time until wilderness warbands starts.
        '''
        addCommand()
        now = datetime.utcnow()
        now = now.replace(microsecond=0)
        lastWarband = now
        jagexTweets = api.user_timeline(screen_name="JagexClock", count=20)
        for tweet in jagexTweets:
            tweetTime = tweet.created_at
            if "Warbands" in tweet.text:
                lastWarband = tweetTime
                lastWarband = lastWarband.replace(second=0)
                break
        timeToWarband = timedelta(hours=7, minutes=15) - (now - lastWarband)
        timeToWarband = timeDiffToString(timeToWarband)
        msg = config['warbandsEmoji'] + " **Wilderness warbands** will begin in " + timeToWarband + "."
        await self.bot.say(msg)

    @commands.command(pass_context=True)
    async def cache(self, ctx):
        '''
        Returns the time until the next Guthixian cache.
        '''
        addCommand()
        now = datetime.utcnow()
        now = now.replace(microsecond=0)
        timeToCache = timedelta(hours=1) - timedelta(minutes=now.minute, seconds=now.second)
        timeToCache = timeDiffToString(timeToCache)
        msg = config['cacheEmoji'] + " **Guthixian caches** will begin in " + timeToCache + "."
        await self.bot.say(msg)

    @commands.command(pass_context=True)
    async def yews(self, ctx):
        '''
        Returns the time until the next divine yews event.
        '''
        addCommand()
        now = datetime.utcnow()
        now = now.replace(microsecond=0)
        timeToYews48 = timedelta(days=1) - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
        timeToYews48 = timeDiffToString(timeToYews48)
        timeToYews140 = timedelta(days=1) - timedelta(hours=((now.hour+6)%24), minutes=now.minute, seconds=now.second)
        timeToYews140 = timeDiffToString(timeToYews140)
        msg = config['yewsEmoji'] + " **Divine yews** will begin in " + timeToYews48 + " in w48 bu, and in " + timeToYews140 + " in w140 bu."
        await self.bot.say(msg)

    @commands.command(pass_context=True)
    async def goebies(self, ctx):
        '''
        Returns the time until the next goebies supply run.
        '''
        addCommand()
        now = datetime.utcnow()
        now = now.replace(microsecond=0)
        timeToGoebies = timedelta(hours=12) - timedelta(hours=(now.hour%12), minutes=now.minute, seconds=now.second)
        timeToGoebies = timeDiffToString(timeToGoebies)
        msg = config['goebiesEmoji'] + " **Goebies supply run** will begin in " + timeToGoebies + "."
        await self.bot.say(msg)

    @commands.command(pass_context=True)
    async def sinkhole(self, ctx):
        '''
        Returns the time until the next sinkhole.
        '''
        addCommand()
        now = datetime.utcnow()
        now = now.replace(microsecond=0)
        timeToSinkhole = timedelta(hours=1) - timedelta(minutes=((now.minute+30)%60), seconds=now.second)
        timeToSinkhole = timeDiffToString(timeToSinkhole)
        msg = config['sinkholeEmoji'] + " **Sinkhole** will spawn in " + timeToSinkhole + "."
        await self.bot.say(msg)

    '''
    @commands.command(pass_context=True)
    async def happyhour(self, ctx):
        addCommand()
        times = [1.0, 9.0, 14.0, 16.5, 21.0]
        now = datetime.utcnow()
        now = now.replace(microsecond=0)
        next = 25.0
        for time in times:
            if time > (now.hour + now.minute/60):
                next = time
                break
        hour = int(next)
        minute = next % 1
        timeToHappyHour = timedelta(hours=hour, minutes=minute) - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
        timeToHappyHour = timeDiffToString(timeToHappyHour)
        msg = config['happyHourEmoji'] + " **Happy Hour** will begin in " + timeToHappyHour + "."
        await self.bot.say(msg)
    '''

def setup(bot):
    bot.add_cog(DNDCommands(bot))
