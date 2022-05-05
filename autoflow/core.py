import os
from typing import List

import autoflow.parsing.syllabic as syllabic
from autoflow.protos.python.bars_pb2 import SongProto

# TODO: spec out and type all of these

class Bars:
    def __init__(self, base_path, syllable_base="NLTK"):
        """
        Base bars path: Path to song directory (e.g. "./macmiller/diablo")
        Song path: Bars path + "song.bars"

        TODO: we should have some nice path management at some point so that we don't have to run the script from a specific spot always!!!
        """
        self._proto = SongProto()
        with open(os.path.join(base_path, "song.bars"), "r") as f:
            self._verses = f.readlines()
        # TODO: song editing --> storing of musical annotation on disk --> use protos and check hash to see if substrate hasn't changed I guess yeah (this goes for hash:words -> syllables and hash:syllables to syllable annotation)
        self._local_override = syllabic.SyllableOverride(base_path) if base_path else None
        self._syllabic_parser = getattr(syllabic, syllabic.BASE_CLASS + syllable_base)(local_override=self._local_override)
        self.parse()

    def to_proto(self) -> SongProto:
        self.parse()
        return self._proto

    def proto_lyrics_hash(self) -> str:
        return "" # TODO: scope out usage / interface / API

    def proto_syllables_hash(self) -> str:
        return "" # TODO: scope out usage / interface / API

    def parse(self):
        del self._proto.bars[:]
        self._proto.bars.extend([self._syllabic_parser.syllabify(line) for line in self._verses if len(line) > 1]) # removing spurious endlines that mess with client side annotations
        self._proto.words = self.gen_lyrics()
        self._proto.syllables = self.gen_syllable_text()

    def gen_lyrics(self):
        verses = ""
        for bar in self._proto.bars:
            for word in bar.words:
                verses += word.word + " "
            verses = verses[:-1] # remove space
            verses += "\n"

        return verses

    def gen_syllable_text(self): # TODO: this should now be deprecated - but test like this for now to make sure functionality is the same and then refactor on swift side
        text_block = ""
        for bar in self._proto.bars:
            for syllable in bar.syllables:
                text_block += syllable.syllable + " "
            text_block = text_block[:-1] # remove space
            text_block += "\n"

        return text_block

    def enumerate_rhymes(self, perfect=True): # TODO: types of rhymes - multi-syllabic etc. - could add list of levels to include - rhyme proto / proto field...? rhyme id for rhyme group / level or sth...
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
        syll.set_offset(offset)
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
