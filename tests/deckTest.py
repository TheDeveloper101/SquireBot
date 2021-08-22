import os
from Tournament import *
from test import *

class DeckTests(TestCase):
    def __init__(self):
        self.testName = "Tournament/deck.py"

    def test(self):
        subTests = []
        
        subTests.append(MoxfieldTest())
        subTests.append(CodFileTest())
        subTests.append(TappedOutTest())
        subTests.append(MtgGoldfishTest())
        subTests.append(BaseCaseTest())
        subTests.append(ExistingDataTest())
        
        testRunner = TestRunner(subTests)
        
        print("[DECK TEST]: Running sub tests...")
        return testRunner.executeTests()
    
class MoxfieldTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/deck.py moxfield tests"
        
    def test(self):
        return True

class CodFileTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/deck.py .cod file tests"
        
    def test(self):
        return True

class TappedOutTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/deck.py tappedout tests"
        
    def test(self):
        return True

class MtgGoldfishTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/deck.py mtgoldfish tests (top 6 from summer bloom 2021)"
        
    def test(self):
        # Top six from summer bloom 2021
        decklinks = ["https://www.moxfield.com/decks/otJGTVMYLE2Tu7dY2eCf3A", "https://www.moxfield.com/decks/BcN9es_OAUaArNr9Yb6-bQ", "https://www.moxfield.com/decks/YlXoO8U2N0qZq7mLrhDqtA", "https://www.moxfield.com/decks/jPilLqEhgk2t1li2haDpCQ", "https://www.moxfield.com/decks/qW5f_UJGBUOxSyhx0sY_Mw", "https://www.moxfield.com/decks/iNtkQTBHW0es9Z_PpE2InA"]
        deckhashes = ["t7rdfct8", "kinva7iq", "s44prtc8", "0sbns7o2", "qvb0eogv", "i0p34cdo"]
        
        assert(len(decklinks) == len(deckhashes))
        for i in range(0, len(decklinks)):
            testdeck = deck("testdeck", decklinks[i])
            if(testdeck.deckHash != deckhashes[i]):
                print(f"Error with moxfield decklist {decklinks[i]}. Hash is {testdeck.deckHash} expecting {deckhashes[i]}. Decklist: '''{testdeck.decklist}'''")
                return False        
        return True

class ExistingDataTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/deck.py test existing data (summer bloom 2021 decks) for hash regression"
    
    def test(self):
        path = f"{os.getcwd()}/test-data-decks"
        for filename in os.listdir(path):
            with open(os.path.join(path, filename), 'r') as f:
                decklist = f.read()
                try:
                    testdeck = deck(filename, decklist)
                except Exception as e:
                    # Catch exception
                    print(f"Error with deck with expected hash {filename} has the wrong hash. Decklist '''{decklist}'''.")
                    raise e
                
                if filename != testdeck.deckHash:
                    print(f"Error with deck with expected hash {filename} has the wrong hash. Decklist '''{decklist}'''. Actual hash: {testdeck.deckHash} Cards: {testdeck.cards}")
                    return False
                    
        return True

class BaseCaseTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/deck.py base case tests"
        
    def test(self):
        deckname = "test-deck"
        deckhash = "u1i483i6"
        
        # Sample format
        decklist1 = """1 Mana Crypt
2 Mana Drain
SB: 1 Mana Vault
SB: 2 White Mana Battery"""

        testdeck = deck(deckname, decklist1)
        assert(testdeck.deckHash == deckhash)
        assert(testdeck.ident == deckname)

        # Cockatrice export non-annotated
        decklist2 = """1 Mana Crypt
2 Mana Drain

1 Mana Vault
2 White Mana Battery"""

        testdeck = deck(deckname, decklist2)
        assert(testdeck.deckHash == deckhash)
        assert(testdeck.ident == deckname)

        # Cockatrice export annotated
        decklist3 = """// 3 Maindeck
// 1 Artifact
1 Mana Crypt

// 2 Instant
2 Mana Drain


// 3 Sideboard
// 3 Artifact
SB: 1 Mana Vault
SB: 2 White Mana Battery"""
        testdeck = deck(deckname, decklist3)
        assert(testdeck.deckHash == deckhash)
        assert(testdeck.ident == deckname)
        
        # Test that deck.py does the cardb lookup
        decklist4 = """2 Glasspool Mimic // Glasspool Shore
SB: 2 Wandering Archaic // Explore the Vastlands"""
        testdeck = deck(deckname, decklist4)
        assert(testdeck.deckHash == "h3jg66ua")
        assert(testdeck.ident == deckname)
        
        return True
