import os
from typing import Dict, List, Optional

import autoflow.parsing.syllabic as syllabic
from autoflow.protos.python.bars_pb2 import SongProto

# TODO: spec out and type all of these

class Bars:
    def __init__(self, base_path, artist_id, song_id, syllable_base="NLTK"):
        """
        Base bars path: Path to song directory (e.g. "./macmiller/diablo")
        Song path: Bars path + "song.bars"

        TODO: we should have some nice path management at some point so that we don't have to run the script from a specific spot always!!!
        """
        self.path = os.path.join(base_path, artist_id, song_id)

        self._proto = SongProto()
        with open(os.path.join(self.path, "song.bars"), "r") as f:
            self._verses = f.readlines()

        # TODO: song editing --> storing of musical annotation on disk --> use protos and check hash to see if substrate hasn't changed I guess yeah (this goes for hash:words -> syllables and hash:syllables to syllable annotation)
        self._local_override = syllabic.SyllableOverride(self.path)
        self._syllabic_parser = getattr(syllabic, syllabic.BASE_CLASS + syllable_base)(local_override=self._local_override)
        self.parse()

        # TODO: check if proto exists
        cached_proto = self.load_proto(base_path, artist_id, song_id)
        if cached_proto is not None:
            # TODO: modes of overwriting
            """
            1. Production - when a line is different, we ignore, so this happens per line
            2. Study - when a song is different at all, we break...? --> offsets get kept... per syllable?
            """
            print(f"Successfully loaded proto, checking validity.")
            # TODO: do line by line checking and overriding
            # TODO: basically build new proto with valid entries from cached proto (cached proto likely overrides syllabic parsing of anything new yea)
            for i, bar in enumerate(self._proto.bars):
                # FIXME: current proto could be longer or shorter than cached proto due to deleted lines... how do we handle this lol
                # NOTE: new proto has word priority -- it's a matter of finding lines in the cached proto that correspond (can always reset line)
                # NOTE: scatted rhythms eventually become separate from the syllables they're tied to, so there's also that form of representation that can be cached / saved out / stored / unmodified
                for j, cached_bar in enumerate(cached_proto.bars):
                    if cached_bar.raw_words == bar.raw_words:
                        print("Words are the same! Checking syllables")
                        if bar.raw_syllables == self._proto.bars[i].raw_syllables:
                            print("TRUE: syllables are the same!")
                        else:
                            print("FALSE: syllables are not the same!") # in this case - likely just roll with it and assume syllabic parsing is frozen (do look into what caused this though in global override --> case is where global override changes word that was fine in this song for whatever reason --> chill if same number of syllables I guess but definitely a weird unlikely case that you should flag)

                        print(f"Overriding proto bar {i} with cached bar {j}") # this will set syllables back once you start unless you hard reset song with button
                        self._proto.bars[i] = cached_proto.bars[j] # TODO: some sort of live tracking of this as you live type - or rather intelligently clear at bar level whenever typing, and on DELETE events handle that accordingly (just delete from the existing proto and don't worry about it -- maybe timings are relative to last beat! and that's the unit... idk this will be obvious as we build this summer)
                        # NOTE: Goal by end of summer - be producing your own songs with this tool from the forms you get from other songs --> 10 hours a week of work (1hr a day == 7 hrs a week + 3 total on weekends) -- same for standup 5 hrs a week -- 1 hr per day~
                        break

            # TODO: if both are same, set beat annotations from proto -- otherwise fail (can also force load if we are confident word --> syllables are frozen! --> only if words have changed should we fully reload)

        # TODO: protos --> rhyming (not now but start to scope out what is best for representing rhyme schemes in edit-proof fashion)

    def parse(self):
        del self._proto.bars[:]
        for i, line in enumerate(self._verses):
            if len(line) > 1:
                parsed_bar = self._syllabic_parser.syllabify(line)
                self._proto.bars.extend([parsed_bar])

    def to_proto(self) -> SongProto:
        self.parse()
        return self._proto

    @staticmethod
    def static_save_proto(base_path, artist_id, song_id, proto: SongProto):
        proto_path = os.path.join(base_path, artist_id, song_id, "song.data")
        with open(proto_path, "wb") as proto_file:
            proto_file.write(proto.SerializeToString())

    @staticmethod
    def load_proto(base_path, artist_id, song_id) -> Optional[SongProto]:
        proto_path = os.path.join(base_path, artist_id, song_id, "song.data")
        if not os.path.exists(proto_path):
            return None

        print("Proto exists, reading.")
        proto = SongProto()
        with open(proto_path, "rb") as proto_file:
            proto.ParseFromString(proto_file.read())

        return proto

    # NOTE: don't need hash - just equality check strings...? could have edge cases but unlikely... just check both words and syllables and if ur g ur g
    # NOTE: this sets the proto.syllabic_hash field (which gets checked on load against syllabic parsing hash) <-- if different need to clear / regen beat / rhyme scheme annotation

    @staticmethod
    def get_artists(base_path) -> Dict[str, str]:
        return {artist : open(os.path.join(base_path, artist, "name.txt")).readline().strip() for artist in os.listdir(base_path) if artist[0] != "_"}

    @staticmethod
    def get_songs(base_path, artist_id) -> Dict[str, str]:
        artist_base = os.path.join(base_path, artist_id)
        return {song : open(os.path.join(artist_base, song, "song.txt")).readline().strip() for song in os.listdir(artist_base) if os.path.isdir(os.path.join(artist_base, song)) and song[0] != "_"}

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
