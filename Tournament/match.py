import xml.etree.ElementTree as ET
import uuid
import threading

import discord

from typing import List, Dict
from enum import IntEnum, auto

from .utils import *


class MatchStatus(IntEnum):
    """ This enum contains the possible statuses of a match. """
    ACTIVE = auto()
    UNCERT = auto()
    CERTIFIED = auto()
    DEAD   = auto()
    UNKNOWN = auto()

class MatchResult(IntEnum):
    """ This enum contains the possible results of a match. This will make it easier to tell if the match was a bye or a draw. """
    NONE = auto()
    WINNER = auto()
    DRAW = auto()
    BYE = auto()
    DEAD = auto()
    UNKNOWN = auto()


class match:
    """ This class stores information about a match, such as its players, winner, and status. """`
    # The class constructor
    def __init__( self, matchNumber: int, a_players: List[str] = None ):
        self.uuid = str( uuid.uuid4() )
        self.saveLocation = ""

        self.matchNumber = matchNumber

        self.activePlayers    = [ ] if a_players is None else a_players
        self.droppedPlayers   = [ ]
        self.confirmedPlayers = [ ]

        self.misfortunes = { }

        self.role   = None
        self.roleID = None
        self.VC     = None
        self.VC_ID  = None

        self.status = MatchStatus.ACTIVE
        self.result = MatchResult.NONE
        self.winner = None

        self.matchLength   = 60*60 # Time is in seconds
        self.timeExtension = 0
        self.timer     = None
        self.startTime = getTime( )
        self.endTime   = None

        # Only changed if it is a trice match
        self.triceMatch = False
        self.playerDeckVerification = False
        self.gameID = -1
        self.replayURL = ""

        self.sentOneMinWarning  = False
        self.sentFiveMinWarning = False
        self.sentFinalWarning   = False

        self.stopTimer = False

    def __lt__(self, other):
        return self.uuid < other.uuid

    def __eq__( self, other ):
        if isinstance( other, match ):
            return False
        # TODO: This needs to be include more of the member values.
        return self.uuid == other.uuid and self.matchNumber == other.matchNumber

    def __str__( self ):
        """ Returns a string representation of the match. """
        digest  = f'Match #{self.matchNumber}\n'
        digest += f'Active players: {", ".join([ p.getMention() for p in self.activePlayers ])}\n'
        digest += f'Dropped players: {", ".join([ p.getMention() for p in self.droppedPlayers ])}\n'
        digest += f'ConfirmedPlayers: {", ".join([ p.getMention() for p in self.confirmedPlayers ])}\n'
        digest += f'Match status: {self._getStatusString()}\n'
        digest += f'Match winner: {self._getWinnerString()}'
        return digest

    def _getStatusString( self ) -> str:
        """ Returns a string containing information about the status of the match. """
        if self.status == MatchStatus.ACTIVE:
            return "Active"
        elif self.status == MatchStatus.UNCERT:
            return "Uncertified"
        elif self.status == MatchStatus.CERTIFIED:
            return "Certified"
        elif self.status == MatchStatus.CLOSED:
            return "Closed"
        elif self.status == MatchStatus.DEAD:
            return "Dead"
        else:
            return "Unknown"

    def _getWinnerString( self ) -> str:
        """ Returns a string containing information about the outcome of the match. """
        if self.result == MatchStatus.NONE:
            return "None"
        elif self.result == MatchStatus.WINNER:
            return self.winner.getMention()
        elif self.result == MatchStatus.BYE:
            return "This match was a bye."
        elif self.result == MatchStatus.DRAW:
            return "This match was a draw."
        else:
            # Should never happen
            return "The result of this much is unknown."

    def isOpen( self ) -> bool:
        """ Determines if the match is active. """
        return self.status == MatchStatus.ACTIVE

    def isUncertified( self ) -> bool:
        """ Determines if the match is uncertified. """
        return self.status == MatchStatus.UNCERT

    def isCertified( self ) -> bool:
        """ Determines if the match is certified. """
        return self.status == MatchStatus.CERTIFIED

    def isDead( self ) -> bool:
        """ Determines if the match is dead. """
        return self.status == MatchStatus.DEAD

    def isBye( self ) -> bool:
        """ Determines if the match was a bye. """
        return self.result == MatchResult.BYE

    def isDraw( self ) -> bool:
        """ Determines if the match was a draw. """
        return self.winner == MatchResult.DRAW

    def getUUID( self ) -> str:
        """ Returns the unique idenifying ID string of the match. """
        return self.uuid

    def getTimeLeft( self ) -> int:
        """ Determines how much time is left in the match. """
        if self.isCertified() or self.stopTimer:
            return -1
        return self.matchLength - round(self.getTimeElapsed()) + self.timeExtension

    def getTimeElapsed( self ) -> float:
        """ Determines how long the match has been active. """
        return timeDiff( getTime(), self.startTime )

    def getMention( self ):
        """ Returns a string that represents the name of the match. """
        if type(self.role) == discord.Role:
            return self.role.mention
        return f'Match #{self.matchNumber}'

    def getMatchNumber( self ) -> int:
        """ Returns the match number for the match. """
        return self.matchNumber

    def giveTimeExtension( self, t: int ) -> None:
        """ Adds a time extension to the match. """
        if self.isCertified() or self.stopTimer:
            return None
        timeLeft = self.getTimeLeft()
        if timeLeft + t > 300 and self.sentFiveMinWarning:
            self.sentFiveMinWarning = False
        if timeLeft + t >  60 and self.sentOneMinWarning:
            self.sentOneMinWarning = False
        self.timeExtension += t

    def addMatchRole( self, a_role: discord.Role ) -> None:
        """ Adds a discord role to the match to store. """
        self.role = a_role

    def addMatchVC( self, a_VC: discord.VoiceChannel ) -> None:
        """ Adds a discord voice channel to the match to store. """
        self.VC = a_VC

    async def killMatch( self ) -> None:
        """ Purges all member data should the match need to be removed. """
        # Note that actually deleting the match is a bad idea as it could cause match numbers to collide.
        if isinstance( self.VC, discord.VoiceChannel ):
            await self.VC.delete()
        if isinstance( self.role, discord.Role ):
            await self.role.delete()

        self.activePlayers    = [ ]
        self.droppedPlayers   = [ ]
        self.confirmedPlayers = [ ]

        self.role   = None
        self.roleID = None
        self.VC     = None
        self.VC_ID  = None

        self.winner = None
        self.status = MatchStatus.DEAD
        self.result = MatchResult.DEAD
        self.endTime = getTime( )
        self.stopTimer = True

    async def confirmMatch( self ) -> bool:
        """ If all conditions are met, the match becomes certified. """
        digest  = len( self.activePlayers    ) == 1
        digest |= len( self.confirmedPlayers ) >= len( self.activePlayers )
        digest &= not self.isCertified( )
        if digest:
            self.status = MatchStatus.CERTIFIED
            self.endTime = getTime( )
            self.stopTimer = True
            if isinstance( self.VC, discord.VoiceChannel ):
                await self.VC.delete()
        return digest

    def recordBye( self ) -> None:
        """ Records the result as a bye. """
        self.endTime = getTime()
        self.stopTimer = True
        self.status = MatchStatus.CERTIFIED
        self.result = MatchResult.BYE
        self.winner = None

    # Confirms the result for one player.
    # If all players have confirmed the result, the status of the match is status to "certified"
    async def confirmResult( self, plyr: "player" ) -> Dict:
        """ Confirms the result for the player. """
        digest = { "message": "" }
        if not self.isUncertified():
            digest["message"] = f'{plyr.getMention()}, a result for match #{self.matchNumber} has not been recorded.'
        elif plyr in self.droppedPlayers:
            digest["message"] = f'{plyr.getMention()}, you have already recorded yourself as losing match #{self.matchNumber}. There is not need to confirm the result.'
        elif plyr in self.confirmedPlayers:
            digest["message"] = f'{plyr.getMention()}, you have already confirmed the result of match #{self.matchNumber}.'
        elif not ( plyr in self.activePlayers or plyr in self.droppedPlayers ):
            difest["message"] = f'{plyr.getMention()}, you are not a player in match #{self.matchNumber}.'
        else:
            self.confirmedPlayers.append( plyr )
            digest["message"] = f'{plyr.getMention()}, your confirmation has been logged.'
            if await self.confirmMatch( ):
                self.stopTimer = True
                digest["announcement"] = f'{self.getMention()}, your match has been certified. You can join the matchmaking queue again.'

        return digest

    async def confirmResultAdmin( self, plyr: "player", mention: str ) -> Dict:
        """ Confirms the result for a player as an admin. """
        # The only major difference is the messages that are returned.
        digest = { "message": "" }
        if not self.isUncertified():
            digest["message"] = f'{mention}, a result for match #{self.matchNumber} has not been recorded.'
        elif plyr in self.confirmedPlayers:
            digest["message"] = f'{mention}, {plyr.getMention()} has already confirmed the result of match #{self.matchNumber}.'
        elif plyr in self.droppedPlayers:
            digest["message"] = f'{mention}, {plyr.getMention()} has already been recorded as losing match #{self.matchNumber}. There is not need to confirm the result for them.'
        elif not ( plyr in self.activePlayers or plyr in self.droppedPlayers ):
            digest["message"] = f'{mention}, {plyr.getMention()} is not a part of match #{self.matchNumber}.'
        else:
            self.confirmedPlayers.append( plyr )
            digest["message"] = f'{mention}, you have logged the confirmation of {plyr.getMention()}.'
            if await self.confirmMatch( ):
                self.stopTimer = True
                digest["announcement"] = f'{self.getMention()}, your match has been certified.'

        return digest

    async def recordResult( self, plyr: "player", result: str ) -> Dict:
        """ Records the result of the match and, if possible, confirms the match. """
        digest = { "message": "" }
        if self.isCertified():
            digest["message"] = f'Match #{self.matchNumber} is already certified. Talk to a tournament official to change the result of this match.'
            return digest

        if "win" == result or "winner" == result:
            self.winner = plyr
            self.result = MatchResult.WINNER
            self.confirmedPlayers = [ plyr ]
            digest["message"] = f'{plyr.getMention()} has recorded themself as the winner of match #{self.matchNumber}. {self.getMention()}, please confirm with "!confirm-result".'
        elif "draw" == result:
            self.result = MatchResult.DRAW
            self.winner = None
            self.confirmedPlayers = [ plyr ]
            digest["message"] = f'{plyr.getMention()} has recorded match #{self.matchNumber} as a draw. {self.getMention()}, please confirm with "!confirm-result".'
        elif "loss" == result or "loser" == result:
            self.droppedPlayers.append( plyr )
            self.activePlayers.remove( plyr )
            digest["message"] = f'{plyr.getMention()}, you have been recorded as losing match #{self.matchNumber}. You will not be able to join the queue until this match is finished, but you will not need to confirm the result.'
        else:
            digest["message"] = f'You have given an invalid result. The possible match results are "win", "draw", and "loss".'
            return digest

        if await self.confirmMatch( ):
            if len(self.activePlayers) == 0:
                self.result = MatchResult.DRAW
                self.winner = None
            elif len(self.activePlayers) == 1:
                self.winner = self.activePlayers[0]
                self.result = MatchResult.WINNER
                self.confirmedPlayers.append( self.winner )
            digest["announcement"] = f'{self.getMention()}, your match has been certified.'
        else:
            self.status = MatchStatus.UNCERT

        return digest

    async def recordResultAdmin( self, plyr: "player", result: str, mention: str ) -> Dict:
        """ Records or overwrites the match result from the match. """
        digest = { "message": "" }

        if not ( plyr in self.activePlayers or plyr in self.droppedPlayers ):
            digest["message"] = f'{mention}, there is no player {plyr.getMention()} in match #{self.matchNumber}.'
            return digest

        # TODO: Each of these pieces should probably be its own method
        if "win" == result or "winner" == result:
            self.winner = plyr
            self.result = MatchResult.WINNER
            digest["announcement"] = f'{self.getMention()}, {plyr.getMention()} has been recorded as the winner of this match.'
            if not self.isCertified( ):
                self.confirmedPlayers = [ plyr ]
                digest["announcement"] += ' Please confirm with "!confirm-result"'
            else:
                digest["announcement"] += ' There is no need to re-confirm the result.'
            digest["message"] = f'{mention}, {plyr.getMention()} has been recorded as the winner of match #{self.matchNumber}.'
        elif "draw" == result:
            self.result = MatchResult.DRAW
            self.winner = None
            digest["announcement"] = f'{self.getMention()}, this match has been recorded as a draw.'
            if not self.isCertified( ):
                self.confirmedPlayers = [ plyr ]
                digest["announcement"] += ' Please confirm with "!confirm-result"'
            else:
                digest["announcement"] += ' There is no need to re-confirm the result.'
            digest["message"] = f'{mention}, match #{self.matchNumber} has been recorded as a draw.'
        elif "loss" == result or "loser" == result:
            if not plyr in self.droppedPlayers:
                self.droppedPlayers.append( plyr )
                self.activePlayers.remove( plyr )
            digest["announcement"] = f'{plyr.getMention()}, you have been recorded as having lost match #{self.matchNumber}. You will not need to confirm the result.'
            digest["message"] = f'{mention}, {plyr.getMention()} has been recorded as having lost match #{self.matchNumber}.'
        else:
            digest["message"] = f'{mention}, you have given an invalid result. The possible match results are "win", "draw", and "loss".'
            return digest

        if await self.confirmMatch( ):
            if len(self.activePlayers) == 0:
                self.winner = None
                self.result = MatchResult.DRAW
            elif len(self.activePlayers) == 1:
                self.winner = self.activePlayers[0]
                self.result = MatchResult.WINNER
                self.confirmedPlayers.append( self.winner )
            digest["announcement"] += f'\n\n{self.getMention()}, your match has been certified.'
        elif not self.isCertified( ):
            self.status = MatchStatus.UNCERT

        return digest

    def _getInnerXMLString( self ) -> str:
        """ Returns the inner part of the XML file. Derived classes will have different inner strings. """
        digest  = ""
        digest += f'\t<uuid>{self.uuid}</uuid>'
        digest += f'\t<number>{self.matchNumber}</number>\n'
        digest += f'\t<matchLength>{self.matchLength}</matchLength>\n'
        digest += f'\t<timeExtension>{self.timeExtension}</timeExtension>\n'
        digest += f'\t<stopTimer>{self.stopTimer}</stopTimer>\n'
        digest += f'\t<startTime>{self.startTime}</startTime>\n'
        digest += f'\t<endTime>{self.endTime}</endTime>\n'
        digest += f'\t<sentWarnings oneMin="{self.sentOneMinWarning}" fiveMin="{self.sentFiveMinWarning}" final="{self.sentFinalWarning}"/>\n'
        digest += f'\t<status>{self.status.name}</status>\n'
        digest += f'\t<result>{self.result.name}</result>\n'
        digest += f'\t<winner>{self.winner.getUUID() if isinstance(self.winner, player) else self.winner}</winner>\n'
        digest += f'\t<triceMatch>{self.triceMatch}</triceMatch>\n'
        digest += f'\t<playerDeckVerification>{self.playerDeckVerification}</playerDeckVerification>\n'
        digest += f'\t<gameID>{self.gameID}</gameID>\n'
        digest += f'\t<replayURL>{self.replayURL}</replayURL>\n'
        digest += '\t<activePlayers>\n'
        for plyr in self.activePlayers:
            digest += f'\t\t<player name="{plyr.getName()}">{plyr.getUUID()}</player>/>\n'
        digest += '\t</activePlayers>\n'
        digest += '\t<droppedPlayers>\n'
        for plyr in self.droppedPlayers:
            digest += f'\t\t<player name="{plyr.getName()}">{plyr.getUUID()}</player>/>\n'
        digest += '\t</droppedPlayers>\n'
        digest += '\t<confirmedPlayers>\n'
        for plyr in self.confirmedPlayers:
            digest += f'\t\t<player name="{plyr.getName()}">{plyr.getUUID()}</player>/>\n'
        digest += '\t</confirmedPlayers>\n'
        return digest

    def saveXML( self, a_filename: str = "" ) -> None:
        """ Saves the match data to an XML file. """
        if a_filename == "":
            a_filename = self.saveLocation
        digest  = "<?xml version='1.0'?>\n"
        digest += f'<match roleID="{self.role.id if type(self.role) == discord.Role else str()}" VC_ID="{self.VC.id if type(self.VC) == discord.VoiceChannel else str()}">\n'
        digest += self._getInnerXMLString( )
        digest += '</match>'
        with open( a_filename, "w+" ) as savefile:
            savefile.write( toSafeXML(digest) )

    def loadXML( self, a_filename: str ) -> None:
        """ Loads the match data from an XML file. """
        self.saveLocation = a_filename
        xmlTree = ET.parse( a_filename )
        matchRoot = xmlTree.getroot()
        self.roleID = fromXML(matchRoot.attrib["roleID"])
        self.uuid = fromXML(matchRoot.find( 'uuid' ).text)
        if self.roleID != "":
            self.roleID = int( fromXML( self.roleID ) )
        self.VC_ID = matchRoot.attrib["VC_ID"]
        if self.VC_ID != "":
            self.VC_ID = int( fromXML( self.VC_ID ) )
        self.matchNumber   = int( fromXML( matchRoot.find( "number" ).text ) )
        self.timeExtension = int( fromXML( matchRoot.find("timeExtension").text ) )
        self.matchLength   = int( fromXML( matchRoot.find( "matchLength" ).text ) )
        self.stopTimer = str_to_bool( fromXML( matchRoot.find("stopTimer").text ) )
        self.startTime = fromXML( matchRoot.find( "startTime") .text )
        self.endTime = fromXML( matchRoot.find( "endTime" ).text )
        self.status = MatchStatus[fromXML( matchRoot.find( "status" ).text )]
        self.result = MatchResult[fromXML( matchRoot.find( "result" ).text )]
        self.triceMatch = str_to_bool( fromXML( matchRoot.find(  "triceMatch" ).text ) )
        self.playerDeckVerification = str_to_bool( fromXML ( matchRoot.find( "playerDeckVerification" ).text ) )
        self.gameID = int( fromXML( matchRoot.find( "gameID" ).text ) )
        self.replayURL = fromXML( matchRoot.find( "replayURL" ).text )
        self.sentOneMinWarning  = str_to_bool( fromXML( matchRoot.find( "sentWarnings" ).attrib["oneMin" ] ) )
        self.sentFiveMinWarning = str_to_bool( fromXML( matchRoot.find( "sentWarnings" ).attrib["fiveMin"] ) )
        self.sentFinalWarning   = str_to_bool( fromXML( matchRoot.find( "sentWarnings" ).attrib["final"  ] ) )
        self.winner = fromXML( matchRoot.find( "winner" ).text )
        for player in matchRoot.find("activePlayers"):
            self.activePlayers.append( fromXML( player.text ) )
        for player in matchRoot.find("droppedPlayers"):
            self.droppedPlayers.append( fromXML( player.text ) )
        for player in matchRoot.find("confirmedPlayers"):
            self.confirmedPlayers.append( fromXML( player.text ) )


from .player import player
