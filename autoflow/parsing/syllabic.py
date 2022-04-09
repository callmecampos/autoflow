# TODO: imports
import abc
import re, json
from nltk import word_tokenize
from nltk.tokenize import SyllableTokenizer
# TODO: try except in case not installed
from syllabipy.legalipy import LegaliPy, getOnsets
from syllabipy.sonoripy import SonoriPy

BASE_CLASS = "Syllabifier"
BACKEND_SONORITY = "sonoripy"
BACKEND_ONSET = "legalipy"

ALPHABET_REGEX = re.compile('[^a-zA-Z]').sub

GLOBAL_OVERRIDE_MAP = {"piano" : ["pi", "a", "no"], "continuum" : ["con", "ti", "nu", "um"], "balance" : ["ba", "lance"], "equilibrium" : ["e", "qui", "li", "bri", "um"], "amphibian" : ["am", "phi", "bi", "an"], "diet" : ["di", "et"], "basements" : ["base", "ments"], "suicide" : ["su", "i", "cide"], "inside" : ["in", "side"], "ok" : ["o", "k"], "cocaine" : ["co", "caine"]}

SINGLE_SYLLABLE_OVERRIDE = set(["love", "eyes", "ain't", "like", "you", "your", "were", "where", "none", "these", "time", "fake", "yeah", "save", "you'll", "come", "made", "leave", "pete", "piece", "wine", "cheese", "some", "are", "make", "lately", "type", "whole", "mine", "here", "sure", "same", "whore", "take", "score", "gave", "more", "fire", "rude", "wise", "peace", "since", "one"])

# TODO: singular basement, but only when it comes up yeah -- worth thinking about simple UI / workflow for this -- gonna involve some amount of iOS dev plus simple callbacks on the server side

# NOTE: plurals and non-plurals (e.g. basement and basements... but also eyes vs eye)

# NOTE: these are general corrections - you might have anunciation specific annotations e.g. "Fake superhero like the *mystry* men" that will need to be handled for that song only (we can ask if it's a syllabifier error or just the anunciation in this verse or song - verse vs. song can set for that song or artist even... hmmm cool song / artist specific overrides)

"""
Other observations: Words that have silent "e" might be misclassified, also plurals and punctutation like apostrophes don't usually change pronunciation, but might cause misclassification, which could be solved by just stripping and adding back or not.
"""
class Syllable:
    """Syllable wrapper class for storing    
 
    @params:
    syllable: [str] syllable primitive string
    bar_offset: [float] phase offset of syllable in bar in the domain [0-1), typically of the form of some sum of (1/2^k) expressions
    duration: [float] duration of syllable in bar of the form 1/2^k, k being a non-negative integer
    pitch: [int] pitch level of spoken syllable (typically defined by song range -- could be a floating point -- yet to decide)
    sigma: [undefined] TO BE IMPLEMENTED: a yet undefined type denoting a jazzy (parameterized) probability distribution applied to the bar offset
    """
    def __init__(self, syllable, bar_offset=None, duration=1/4, pitch=0, sigma=None):
        # TODO: add IPA / Arpabet representation for rhyming etc. - for loose rhymes can diverge from official
        self.syllable = syllable
        self._bar_offset = bar_offset
        self._duration = duration
        self._pitch = pitch

        self._jazztribution = sigma

    def set_bar_offset(self, val):
        self._bar_offset = val # check valid - maybe tied to another dictionary

    def set_duration(self, val):
        self._duration = val

    def set_pitch(self, val): # TODO: could also set as int over max and make self._pitch a float (get will take in that max and return an int)
        self._pitch = val
    
    def set_jazztribution(self, jazz):
        self._jazztribution = jazz # type this somehow : general distributions??? gaussian, poisson, general multimodal, etc.

    def get_bar_offset(self, jazzy=False):
        return self._bar_offset if not jazzy else self._bar_offset + self._jazztribution.sample()

    def get_duration(self):
        return self._duration

    def get_pitch(self):
        return self._pitch

    # TODO: return possible IPA representations (or pass into constructor the correct one)
    # TODO: return possible rhymes -- this gets to a SyllableGroup class which groups together syllables with these same methods -- just slightly diff implementation

    def valid(self):
        return isinstance(self._bar_offset, float) and 0 <= self._bar_offset < 1 # and others 

    def __repr__(self):
        return f"{self.syllable} + (Offset {self._bar_offset} for {self._duration} pitched at {self._pitch} (jazzy: {self._jazztribution is not None}))"

class Syllabifier(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def _syllabify(self, word):
        pass

    def _syllabify_override(self, word): # TODO: add return descriptors (e.g. Optional[Syllable] here)
        word = ALPHABET_REGEX('', word)
        if len(word) == 0:
            return []
        return GLOBAL_OVERRIDE_MAP.get(word) or ([word] if word in SINGLE_SYLLABLE_OVERRIDE else self._syllabify(word))

    def syllabify(self, line, _nltk=False, _rstrip=True, _generate=False): # TODO: compare different options -- does _ntlk change behavior with/without rstrip? do some python -i testing
        if _rstrip:
            line = line.rstrip()
        line = line.replace("-", " ") # TODO: consider making this an option? might be fine to pass in dashes or nah if u change architecture - could be set in initializer with abstract class defaults ya know
        words = word_tokenize(line) if _nltk else line.split(" ") # optional split by dash and " " (or other symbols that are custom-defineable)
        syllable_pack = []
        for word in words: # TODO: ntlk word tokenizer acts differently than simple split by " "
            syllable_pack.extend([Syllable(s) for s in self._syllabify_override(word.lower()) if s is not None])
            # TODO: maybe have override be optional... or can override the override dictionary with your own or an artist / song specific one? this might be part of metadata pbtxt
        
        return syllable_pack

class SyllabifierNLTK(Syllabifier):
    def __init__(self):
        self.tokenizer = SyllableTokenizer()
        
    def _syllabify(self, word):
        return self.tokenizer.tokenize(word)

class SyllabifierHenchPy(Syllabifier):
    def __init__(self, backend=BACKEND_SONORITY, onset_text=None):
        if backend == BACKEND_SONORITY:
            self.tokenize = SonoriPy
        elif backend == BACKEND_ONSET:
            assert onset_text is not None, "onset_text is None"
            self.tokenize = lambda word: LegaliPy(word, getOnset(onset_text))
        else:
            raise Exception(f"Invalid HenchPy backend: {backend}")

    def _syllabify(self, word):
       return self.tokenize(word) 
