import os
from typing import List 

import autoflow.parsing.syllabic as syllabic

# TODO: spec out and type all of these

class Bars:
    def __init__(self, verses, options={syllabic.BASE_CLASS : "NLTK"}):
        self._verses = verses
        self._options = options # TODO: quick way to validate this (check keys at base -- and validity of it otherwise -- parse could just fail if invalid type deal)
        self.parse(init=True)

    @classmethod
    def load(cls, bars_path):
        """
        Bars path: Path to song directory (e.g. "./macmiller/diablo")
        Song path: Bars path + "song.bars"
        """
        with open(os.path.join(bars_path, "song.bars"), "r") as f:
            return cls(f.readlines())

    def parse(self, init=False):
        if init:
            self.syllabic_parser = getattr(syllabic, syllabic.BASE_CLASS + self._options[syllabic.BASE_CLASS])()
        self._parsed_verses = [self.syllabic_parser.syllabify(line) for line in self._verses]
        # TODO: implement - loop through verses and build parsed_verses instance variable... what is a good representation for this?

    def verses(self, raw=True):
        return ''.join(self._verses) if raw else self._verses

    def syllable_text(self):
        text_block = ""
        for line in self._parsed_verses:
            for syllable in line:
                text_block += syllable.syllable + " "
            text_block = text_block[:-1] # remove space
            text_block += "\n"

        return text_block

    def enumerate_rhymes(self, perfect=True): # TODO: types of rhymes - multi-syllabic etc.
        # TODO: use a window of some sort to do a simple matching of phonetic similarity within some threshold (definitely exist apis / methods for this) -- double for loop is naturally the easiest
        pass

class Bar:
    """Bar class for a single bar (line) of a song in 4/4 meter

    Used by user interface calls (or another interfacing system) to modify syllabic components of a bar in rhythm, duration, pitch (or others aka IPA representation)

    NOTES:
    - TODO: Can be converted to a proto / serialized objects of sorts in a versioned system representation (which can also be interfaced with through loading and writing)
    """
    def __init__(self, syllabic_line : List[syllabic.Syllable]):
        self.syllabic_line = syllabic_line

    def set_syllable(self, index, offset, duration=1/4, pitch=0):
        syll = self.syllabic_line[index]
        syll.set_bar_offset(offset)
        syll.set_duration(duration)
        syll.set_pitch(pitch)

    """ MARK: Human Correction (let's make sure this is mostly frozen before musical annotation - we'll have to be careful about how we handle that) """

    def split_syllable(self, syll, letter):
        # This should call syll.split(letter) but do the relevant replacement in the list with the returned values
        pass # TODO: splits syllable at given letter (we should think of a raw vs. edited proto representation) -- e.g. for diet --> di et

    def join_syllables(self, syll1, syll2): # maybe take in arbitrary number of syllables in args and join
        pass

    def split_beat(self, start, end, ratio):
        # FIXME: this will go closer to a UI layer
        pass # NOTE: this feels like more of a UI thing - the idea being that with the lyrical chart UI it'll start with 4 split beats in a bar (aligned to increments of 1/4) and that the user can split from there with some UI action -- this does need to be stored, but maybe not at this level...

    # what other actions?

"""
Questions:
Do syllables maybe map to general meter segments? (e.g. base + ... + 1/2^k) Yes, generally k in [0, 5]
Yes - can add some jazzy annotation if needed (random before / after -- maybe not just gaussian -- jazzian)

What is a useful UI for mapping syllabic repr. into rhythmic repr.?
Several different modes:
1. Tapping on the beat with each successive tap incrementing the syllable we're looking at (this can be iterative --> stopping and starting and re-aligning --> provides a first order initialization almost --> this can likely be automated with something like https://github.com/deezer/spleeter and mapping transients in the Fourier domain to syllable speaking --> another first order initialization --> on the manual side this requires a temporal reference to start at for correct meter alignment) --> GarageBand has a great example of this -- should be chill to re-engineer with rests auto-filled etc.
2. Tying (with line or successive taps -- AutoLayout-esque) syllabic components to meter buckets (can further split or manually define if desired -- different ways of doing this)
3. There's always just manual typing / setting in a UI box popping out of the syll / rhythmic repr

How do we think about rhyme annotation?
1. IPA / ArpaBet repr.
2. Manual adjustments
3. Initialization from spleeter and NLP mapping spoken word sound to IPA type deal

Alignment of music to bar (or smaller units)?
Bar - MusixMatch API
Smaller units - custom? through UI? some basic manually set infra that let's us infer the rest -- we have already the words (some alignment) + the audio -- NLP that constrained bih

NEXT STEPS:
1. Start making a simple UI that allows you to load (HTTP GET) desired / available songs (later we can think about putting in our own)
2. Have a button that taps and times your taps and builds notes from that with MusicKit (can be sent back and checked with LilyPond -- LP used for server-side repr / rendering / checking -- MK used for client side)
3. Flask server that returns back renders of tapped notes... (requires some sort of note type that we can parse into Abjad repr.)

Metrics:
1. Syllables per beat (i.e. SPM vs. BPM -- Easy Rider, per artist what are the distributions of these relative to beats they rap on - is it consistent?)
"""
