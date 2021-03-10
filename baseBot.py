import os

import discord
import random
from random import getrandbits
from discord import Activity, ActivityType
from discord.ext import commands
from dotenv import load_dotenv


from Tournament import *

#async def sendAdminHelpMessage( ctx ) -> None:

async def sendUserHelpMessage( ctx ) -> None:
    embed = discord.Embed( )
    embed.add_field( name="Overview", value="Below, you'll find a brief description of this bot's commands. You can find a more detailed list [here](https://docs.google.com/document/d/1-ducYUYXel8vDJeDjY9ePYN36kF5Q8jTnbBck8Qjuoc/edit?usp=sharing). There is also a [crash course](https://docs.google.com/document/d/1jOWfZjhhxOai7CjDqZ6fFnio3qRuLa0efg9HeEiG6MA/edit?usp=sharing). If you have ideas about how to improve this bot, [let us know](https://forms.gle/jt9Hpaz3ZcVNfeiRA)!",inline=False )
    
    regDigest = "- register : Registers you for a tournament\n\
                 - add-deck : Registers a deck for a tournament (should be sent via DM)\n\
                 - remove-deck : Removes a deck you registered\n\
                 - list-decks : Lists the names and hashes of the decks you've registered\n\
                 - cockatrice-name : Adds your Cockatrice username to your profile\n\
                 - drop : Removes you from the tournament"
    embed.add_field( name="Registration Commands", value=regDigest, inline=False )
    
    matchDigest = "- lfg : Places you into the matchmaking queue\n\
                   - match-result : Records you as the winner of your match or that the match was a draw\n\
                   - confirm-result : Records that you agree with the declared result"
    embed.add_field( name="Match Commands", value=matchDigest,inline=False )
    
    miscDigest = "- standings : Prints out the current standings\n\
                  - misfortune : Helps you resolve Wheel of Misfortune."
    embed.add_field( name="Miscellaneous Commands", value=miscDigest,inline=False )
    
    await ctx.send( embed=embed )
    return


async def isPrivateMessage( ctx, send: bool = True ) -> bool:
    digest = (str(ctx.message.channel.type) == 'private')
    if digest and send:
        await ctx.send( f'You are not allowed to send commands via DM other than "!add-deck". Please send your command in the Discord server that is hosting your tournament.' )
    return digest

async def isTournamentAdmin( ctx, send: bool = True ) -> bool:
    digest = False
    adminMention = getTournamentAdminMention( ctx.message.guild )
    for role in ctx.message.author.roles:
        digest |= str(role).lower() == "tournament admin"
    if not digest and send:
        await ctx.send( f'{ctx.message.author.mention}, invalid permissions: You are not tournament staff. Please do not use this command again or {adminMention} may intervene.' )
    return digest

async def checkTournExists( tourn, ctx, send: bool = True ) -> bool:
    digest = ( tourn in tournaments )
    if not digest and send:
        await ctx.send( f'{ctx.message.author.mention}, there is no tournament named "{tourn}" in this server.' )
    return digest

async def correctGuild( tourn, ctx, send: bool = True ) -> bool:
    digest = ( tournaments[tourn].hostGuildName == ctx.message.guild.name )
    if not digest and send:
        await ctx.send( f'{ctx.message.author.mention}, this server is not hosting {tourn}. Please send your command in the correct server.' )
    return digest

async def isTournDead( tourn, ctx, send: bool = True ) -> bool:
    adminMetnion = getTournamentAdminMention( ctx.message.guild )
    digest = tournaments[tourn].isDead( )
    if digest and send:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} has ended or been cancelled. Contact {adminMention} if you think this is an error.' )
    return digest

async def isTournRunning( tourn, ctx, send: bool = True ) -> bool:
    digest = tournaments[tourn].isActive and not await isTournDead( tourn, ctx, send )
    if send and not tournaments[tourn].isActive:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} has not started yet.' )
    return digest

async def isRegOpen( tourn, ctx, send: bool = True ) -> bool:
    digest = tournaments[tourn].regOpen
    if send and not digest:
        await ctx.send( f'{ctx.message.author.mention}, registration for {tourn} is closed. Please contact tournament staff if you think this is an error.' )
    return digest

async def hasRegistered( tourn, plyr, ctx, send: bool = True ) -> bool:
    digest = plyr in tournaments[tourn].players
    if send and not digest:
        await ctx.send( f'{ctx.message.author.mention}, you are not registered for {tourn}. Please register before trying to access the tournament.' )
    return digest
        
async def isActivePlayer( tourn, plyr, ctx, send: bool = True ) -> bool:
    digest = tournaments[tourn].players[plyr].isActive( )
    if send and not digest:
        await ctx.send( f'{ctx.message.author.mention}, you registered for {tourn} but have been dropped. Contact tournament staff if you think this is an error.' )
    return digest
    
async def hasOpenMatch( tourn, plyr, ctx, send: bool = True ) -> bool:
    digest = tournaments[tourn].players[plyr].hasOpenMatch( )
    if send and not digest:
        await ctx.send( f'{ctx.message.author.mention}, you are not an active player in a match. You do not need to do anything.' )
    return digest

async def hasCommandWaiting( ctx, a_user: str, send: bool = True ) -> bool:
    digest = a_user in commandsToConfirm
    if send and digest:
        await ctx.send( f'{ctx.message.author.mention}, you have a command waiting for your confirmation. That confirmation request is being overwriten by this one.' )
    return digest

def getTournamentAdminMention( a_guild ) -> str:
    adminMention = ""
    for role in a_guild.roles:
        if str(role).lower() == "tournament admin":
            adminMention = role.mention
            break
    return adminMention

def currentGuildTournaments( a_guildName: str ):
    tourns = {}
    for tourn in tournaments:
        if not tournaments[tourn].isDead() and tournaments[tourn].hostGuildName == a_guildName:
            tourns[tourn] = tournaments[tourn]
    return tourns

def hasStartedTournament( a_guildName ) -> bool:
    for tourn in tournaments:
        if tournaments[tourn].tournStarted and tournaments[tourn].hostGuildName == a_guildName:
            return True
    return False

def findGuildMember( a_guild: discord.Guild, a_memberName: str ):
    for member in a_guild.members:
        if member.display_name == a_memberName:
            return member
        if member.mention == a_memberName:
            return member
    return ""
    
def findPlayer( a_guild: discord.Guild, a_tourn: str, a_memberName: str ):
    role = discord.utils.get( a_guild.roles, name=f'{a_tourn} Player' )
    if type( role ) != discord.Role:
        return ""
    for member in role.members:
        if member.display_name == a_memberName:
            return member
        if member.mention == a_memberName:
            return member
        if f'<@!{member.id}>' == a_memberName:
            return member
        if f'<@{member.id}>' == a_memberName:
            return member
    return ""

def splitMessage( msg: str, limit: int = 2000, delim: str = "\n" ) -> List[str]:
    if len(msg) <= limit:
        return [ msg ]
    msg = msg.split( delim )
    digest = [ "" ]
    for submsg in msg:
        if len(digest[-1]) + len(submsg) <= limit:
            digest[-1] += delim + submsg
        else:
            digest.append( submsg )
    return digest
    

MAX_COIN_FLIPS = 2**19

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

random.seed( )

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

tournaments = {}

# A dictionary indexed by user idents and consisting of creation time, duration, and a coro to be awaited
commandsToConfirm = { }

playersToBeDropped = []

savedTournaments = [ f'currentTournaments/{d}' for d in os.listdir( "currentTournaments" ) if os.path.isdir( f'currentTournaments/{d}' ) ]


# When ready, the bot needs to looks at each pre-loaded tournament and add a discord user to each player.
@bot.event
async def on_ready():
    await bot.wait_until_ready( )
    print(f'{bot.user.name} has connected to Discord!\n')
    for guild in bot.guilds:
        print( f'This bot is connected to {guild.name} which has {len(guild.members)}!' )    
    print( "" )
    for tourn in savedTournaments:
        newTourn = tournament( "", "" )
        newTourn.loop = bot.loop
        newTourn.loadTournament( tourn )
        if newTourn.tournName != "":
            tournaments[newTourn.tournName] = newTourn
    for tourn in tournaments:
        guild = bot.get_guild( tournaments[tourn].guildID )
        if not guild is None:
            tournaments[tourn].assignGuild( guild )
            tournaments[tourn].loop = bot.loop


@bot.command(name='test')
async def test( ctx, *args ):
    if ctx.message.author.id != int( os.getenv( "TYLORDS_ID" ) ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permission to use this command. Contact Tylord2894 to learn more.' )
        return
    
    codes = (await ctx.message.attachments[0].read()).decode("utf-8").split( "\n" )
    
    await ctx.send( "This is the content of the file (line-by-line)." )
    for code in codes:
        if len(code.strip()) != 0:
            await ctx.send( code )


@bot.command(name='send-codes')
async def sendCodes( ctx, *args ):
    if ctx.message.author.id != int( os.getenv( "TYLORDS_ID" ) ):
        await ctx.send( f'{ctx.message.author.mention}, you do not have permission to use this command. Contact Tylord2894 to learn more.' )
        return
    
    if len(args) < 1:
        await ctx.send( f'{ctx.message.author.mention}, specify a tournament.' )
        return
    
    codes = [ code for code in (await ctx.message.attachments[0].read()).decode("utf-8").split( "\n" ) if len(code.strip()) != 0 ]
    
    if len(codes) < len(tournaments[args[0]].players):
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough codes. You provided {len(codes)} codes but there are {len(tournaments[args[0]].players)} players (dropped and active) in {args[0]}.' )
        return
    
    if len(codes) > len(tournaments[args[0]].players):
        await ctx.send( f'{ctx.message.author.mention}, you provided more than enough codes. You provided {len(codes)} codes but there are {len(tournaments[args[0]].players)} players (dropped and active) in {args[0]}. The codes will be sent, but some will go unused.' )
    
    await ctx.send( "Sending codes." )
    players = list( tournaments[args[0]].players.values() )
    for i in range(len(players)):
        try:
            await players[i].discordUser.send( content=f'Thank you for playing in {args[0]}!! As a thank you, here is a code for an Altar Sleeve, which is redemable [here], {codes[i]}.' )
        except:
            await ctx.send( f'There was an issue sending a code to {players[i].name}' )
    await ctx.send( "All codes have been sent" )
    

bot.remove_command( "help" )
@bot.command(name='help')
async def printHelp( ctx ):
    if await isPrivateMessage( ctx, send=False ):
        ctx.send( f'There are two commands that you can use via DM, "!add-deck" and "!misfortune".' )
        return

    #if await isTournamentAdmin( ctx, send=False ):
        #sendAdminHelpMessage( ctx )
    #else:
    await sendUserHelpMessage( ctx )


@bot.command(name='flip-coins')
async def flipCoin( ctx, num ):
    try:
        num = int( num.strip() )
    except:
        await ctx.send( f'{ctx.message.author.mention}, you need to specify a number of coins to flip (using digits, not words).' )
        return
    
    if num > MAX_COIN_FLIPS:
        await ctx.send( f'{ctx.message.author.mention}, you specified too many coins. I can flip at most {MAX_COIN_FLIPS} at a time. I will flip that many, but you still need to have {num - MAX_COIN_FLIPS} flipped.' )
        num = MAX_COIN_FLIPS
    
    count = 0
    tmp = getrandbits( num )
    for i in range( num ):
        if 1<<i & tmp != 0:
            count += 1
    
    await ctx.send( f'{ctx.message.author.mention}, out of {num} coin flip{"" if num == 1 else "s"} you won {count} time{"" if count == 1 else "s"}.' )


@bot.command(name='yes')
async def confirmCommand( ctx ):
    userIdent = getUserIdent( ctx.message.author )
    if not userIdent in commandsToConfirm:
        await ctx.send( f'{ctx.message.author.mention}, there are no commands needing your confirmation.' )
        return
    
    if commandsToConfirm[userIdent][1] <= timeDiff( commandsToConfirm[userIdent][0], getTime() ):
        await ctx.send( f'{ctx.message.author.mention}, you waited too long to confirm. If you still wish to confirm, run your prior command and then confirm.' )
        del( commandsToConfirm[userIdent] )
        return
    
    message = await commandsToConfirm[userIdent][2]
    # Check to see if the message is from endTourn or cancelTourn
    # If so, the tournament needs to be cancelled
    if "has been closed" in message or "has been cancelled" in message:
        words = message.split( "," )[1].strip().split( " " )
        for i in range(1,len(words)-1):
            if words[i] == "has":
                if words[i+1] == "been":
                    tourn = " ".join( words[:i] )
                    break
        del( tournaments[tourn] )
    await ctx.send( message )
    del( commandsToConfirm[userIdent] )


@bot.command(name='no')
async def denyCommand( ctx ):
    print( commandsToConfirm )
    userIdent = getUserIdent( ctx.message.author )
    if not userIdent in commandsToConfirm:
        await ctx.send( f'{ctx.message.author.mention}, there are no commands needing your confirmation.' )
        return
    
    await ctx.send( f'{ctx.message.author.mention}, your request has been cancelled.' )

    del( commandsToConfirm[userIdent] )


