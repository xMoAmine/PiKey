from metagame import *
from ddr import *
from cmd import *
from pimidi import *
from piece import *
import pygame
import midi as MIDI # van python-midi vishnubob github, voor het makkelijk "reading/writing" van midi bestanden.
import config
from collections import deque # voor het snel poppen van lists.
import itertools
import mingus.core.chords as CHORDS
import mingus.core.notes as NOTES

class EditClass( DDRClass ): # erft van de DDR class.
#### EDIT CLASS
    def __init__( self, piecedir, midi, piecesettings = { 
            "TempoPercent" : 100, "Difficulty" : 0,
            "BookmarkTicks" : [],
            "AllowedDifficulties" : [ 0 ],
            "Sandbox" : config.SANDBOXplay,
            "PlayerStarts" : config.PLAYERstarts,
            "PlayerTrack" : 0,
            "Metronome" : config.METRONOMEdefault } ):
        DDRClass.__init__( self, piecedir, midi, piecesettings )
        self.noteson = {} # notes die je inklikt en na een bepaalde tijd uitgaan.
        self.sandbox = 1 # in edit mode moet je 100% Sandbox zijn gang laten gaan, alles gaat mis als dit niet zo is.
        self.currentvelocity = 100 # standaard note velocity.
        self.currenttrack = 0
        self.noteclipboard = [] # voor copy pasting
    
        # set the default state of the editor
        self.allowedchanges = [ 'state' ]
        self.state = -1
        #self.EXITstate = 0 # 
        self.NAVIGATIONstate = 1 # standaard staat als je escape inklikt.  voor copy/pasting, etc.  
        self.SELECTstate = 2 # visual block/line type stuff
        self.COMMANDstate = 3 # after pressing escape, then colon (:).  vim-like command mode
        self.INSERTstate = 4 # nadat je i,I, a,A, inklikt kan je noten maken op je keyboard
        self.CHORDstate = 5 

        self.commandlist = deque([], config.COMMANDhistory) 
        self.commandlistindex = -1
        self.commandfont = config.FONT
        self.commandfontcolor = (255,255,255)
        self.commandfontsize = int(24*config.FONTSIZEmultiplier)
        self.commandbackcolor = (0, 0, 0)
        self.helperfontcolor = (255,255,255)
        self.helperfontsize = int(18*config.FONTSIZEmultiplier)
        self.helperbackcolor = (0, 0, 0)
        self.statenames = { self.NAVIGATIONstate : "Navigation",
                            self.SELECTstate : "Select",
                            self.COMMANDstate : "Command",
                            self.INSERTstate : "Insert",
                            self.CHORDstate : "Chord" }
        self.helper = { 
            self.NAVIGATIONstate : [ 0, #start line
                 [ " ctrl+j|k   scroll deze helper lijst down|up",
                   "   ctrl+/   search deze helper lijst",
                   " ctrl+n|N   herhaal het zoeken forward|backward",
                   "",
                   "  h|j|k|l   beweeg left|down|up|right",
                   "  H|J|K|L   beweeg left|down|up|right faster",
                   "      g|G   ga naar beginning|end van de piece",
                   "    SPACE   start/stop piece playing",
                   "",
                   "        y   yank (copy) notes with any overlap",
                   "      e|E   verleng noten bij half|full ",
                   "        s   verklein noten",

                   "",
                   "  PgUp|Dn   beweeg up|down met een scherm",
                   " HOME|END   beweeg helemaal naar left|right links of rechts",
                    ]
               ],
            self.SELECTstate : [ 0, #start line
                 [ "ctrl+j|k    scroll deze helper lijst down|up",
                   " h|j|k|l    beweeg left|down|up|right" ]
               ],
            self.COMMANDstate : [ 0, #start line
                 [ "ctrl+j|k    scroll deze helper lijst down|up",
                   "  ESCAPE    go terug naar navigation mode",
                   " up|down    navigeer command history",
                   " PgUp|Dn    verwijder command",
                   " ",
                   "Typ en klik enter:",
                   "  q|quit    sluit PiKey",
                   "s|save|w    save piece",
                   "  return    terug naar main menu ",
                   "  reload    herhaal de piece van de safe file",
                   "   clear    leeg de piece",
                   "",
                   "     i X    verander instrument naar X,"
                   "            X kan een nummer van (0 to 127) zijn, of een naam",
                   "     v X    set quick-input velocity to X (0 to 127)",
                   "     o X    open difficulty X",
                   ]
               ],
            }

        # in deze helper zie je al je commands die je kan gebruiken als je "escape" inklikt -  escape maakt je cmd aka command prompt open.
        self.helperlines = [] 
        self.lasthelpsearched = ""
        self.helperlinemax = max(1, config.HELPERLINEmax)

        self.setstate( state=self.NAVIGATIONstate )

        # de onderste variabele zijn voor de bovengenoemde onderdelen.:
        self.insertmode = 0    
        self.waitforkeytoplay = 0

        # om de helper te krijgen en command informatie te krijgen
        self.commander = CommandClass( self.docommand, "cmd" )
        self.chordcommander = CommandClass( self.addquickchordinselection, "quick chord" )
        
        self.preemptor = None
        #self.preemptingfor = { 
            #"search help" : CommandClass( self.searchhelp, "search help" ),
            #"scale factor" : CommandClass( self.scalecursorselection, "scale factor" )
        #}

        self.anchor = 0 #gaat naar [ midinote, anchorposition ]

#### END