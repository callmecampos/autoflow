# TODO: imports
import abc, shortuuid
from pickle import GLOBAL
import re, json, os
from typing import List, Dict, Set
from nltk import word_tokenize
from nltk.tokenize import SyllableTokenizer
# TODO: try except in case not installed -- fine for now
from syllabipy.legalipy import LegaliPy, getOnsets
from syllabipy.sonoripy import SonoriPy

from autoflow.protos.python.bars_pb2 import SongProto, BarProto, WordProto, SyllableProto

BASE_CLASS = "Syllabifier"
BACKEND_SONORITY = "sonoripy"
BACKEND_ONSET = "legalipy"

ALPHABET_REGEX = re.compile('[^a-zA-Z]').sub

"""
TODO:
Override object (global from bars directory, or artist specific, should be an easy API to call and add to (and do fine edits and write back)
For now we can manually version control (git add to whole repo to staging)

Goal: Have API where the frontend can add overrides for words!!!

UI req: selections need to be part of the same word

Backend req: syllable has reference to word id / idx so that they can check
"""

"""
- json vs. proto storage? proto storage harder to edit manually... maybe just proto to json simple function... or just keep it as json for now
"""

GLOBAL_MULTI_OVERRIDE = {"piano" : ["pi", "a", "no"], "continuum" : ["con", "ti", "nu", "um"], "balance" : ["ba", "lance"], "equilibrium" : ["e", "qui", "li", "bri", "um"], "amphibian" : ["am", "phi", "bi", "an"], "diet" : ["di", "et"], "basements" : ["base", "ments"], "suicide" : ["su", "i", "cide"], "inside" : ["in", "side"], "ok" : ["o", "k"], "cocaine" : ["co", "caine"]}

GLOBAL_SINGLE_OVERRIDE = set(["love", "eyes", "ain't", "like", "you", "your", "were", "where", "none", "these", "time", "fake", "yeah", "save", "you'll", "come", "made", "leave", "pete", "piece", "wine", "cheese", "some", "are", "make", "lately", "type", "whole", "mine", "here", "sure", "same", "whore", "take", "score", "gave", "more", "fire", "rude", "wise", "peace", "since", "one"])

# TODO: singular basement, but only when it comes up yeah -- worth thinking about simple UI / workflow for this -- gonna involve some amount of iOS dev plus simple callbacks on the server side

# NOTE: plurals and non-plurals (e.g. basement and basements... but also eyes vs eye)

# NOTE: these are general corrections - you might have anunciation specific annotations e.g. "Fake superhero like the *mystry* men" that will need to be handled for that song only (we can ask if it's a syllabifier error or just the anunciation in this verse or song - verse vs. song can set for that song or artist even... hmmm cool song / artist specific overrides)

"""
Other observations: Words that have silent "e" might be misclassified, also plurals and punctutation like apostrophes don't usually change pronunciation, but might cause misclassification, which could be solved by just stripping and adding back or not.
"""

class SyllableOverride:
    MULTI_OVER_JSON = "multi.json"
    SINGLE_OVER_JSON = "single.json"

    @staticmethod
    def obj_to_json(obj, path):
        j = json.dumps(obj, indent=2)
        with open(path, "w+") as f:
            f.write(j)

        return j

    @staticmethod
    def obj_from_json(path):
        with open(path, "r") as f:
            return json.load(f)

    def __init__(self, base_path="./bars", default_multi={}, default_single=set([])):
        self.base_path = os.path.join(base_path, "_syllable")
        os.makedirs(self.base_path, exist_ok=True)
        if (not os.path.exists(self.multi_override_path())):
            print(f"Multi override does not exist ({self.multi_override_path()}), creating.")
            self.set_multi_override(default_multi)
        if (not os.path.exists(self.single_override_path())):
            print(f"Single override does not exist ({self.single_override_path()}), creating.")
            self.set_single_override(default_single)

    def multi_override_path(self):
        return os.path.join(self.base_path, self.MULTI_OVER_JSON)

    def single_override_path(self):
        return os.path.join(self.base_path, self.SINGLE_OVER_JSON)

    def get_multi_override(self) -> Dict[str, str]:
        return self.obj_from_json(self.multi_override_path())

    def get_single_override(self) -> Set[str]:
        return set(self.obj_from_json(self.single_override_path()))

    def set_multi_override(self, over: Dict[str, str]):
        self.obj_to_json(over, self.multi_override_path())

    def set_single_override(self, over: Set[str]):
        self.obj_to_json(list(over), self.single_override_path())

    def add_override(self, word: str, syllables: List[str]):
        assert len(syllables), f"{word} | {syllables}"
        assert word == ''.join(syllables), f"{word} | {''.join(syllables)}" # this may not be true depending on whether word is pre-stripped
        if len(syllables) == 1:
            single_over = self.get_single_override()
            single_over.add(word)
            self.set_single_override(single_over)
        else:
            multi_over = self.get_multi_override()
            multi_over[word] = syllables
            self.set_multi_override(multi_over)

class Syllable:
    """Syllable wrapper class for storing    
 
    @params:
    syllable: [str] syllable primitive string
    bar_offset: [float] phase offset of syllable in bar in the domain [0-1), typically of the form of some sum of (1/2^k) expressions
    duration: [float] duration of syllable in bar of the form 1/2^k, k being a non-negative integer
    pitch: [int] pitch level of spoken syllable (typically defined by song range -- could be a floating point -- yet to decide)
    sigma: [undefined] TO BE IMPLEMENTED: a yet undefined type denoting a jazzy (parameterized) probability distribution applied to the bar offset
    """
    @staticmethod
    def proto(syllable: str, parent_word: WordProto,
                bar_offset: float = None, duration: float = None, pitch: float = 0) -> SyllableProto:
        _proto = SyllableProto()
        _proto.syllable = syllable
        _proto.parent_word.CopyFrom(parent_word)
        if bar_offset is not None:
            _proto.offset = bar_offset
        if duration is not None:
            _proto.duration = duration
        _proto.pitch = pitch # NOTE: pitch should likely come directly from song, though maybe we can abstract it here -- ideally predicted / extracted exactly from audio though with a neural net... or neural net for extracting lyrics audio which then measures natural pitch mean for syll or whatnot idk
        return _proto

    @classmethod
    def create(cls, syllable: str, parent_word: WordProto,
                bar_offset: float = None, duration: float = 1/4, pitch: float = 0):
        return cls(Syllable.proto(syllable, parent_word, bar_offset, duration, pitch))

    def to_proto(self) -> SyllableProto:
        return self._proto

    def __init__(self, syllable_proto: SyllableProto):
        # TODO: add IPA / Arpabet representation for rhyming etc. - for loose rhymes can diverge from official
        self._proto = syllable_proto

    def set_syllable(self, val: str):
        self._proto.syllable = val

    def set_offset(self, val: float):
        self._proto.offset = val # check valid - maybe tied to another dictionary

    def set_duration(self, val: float):
        self._proto.duration = val

    def set_pitch(self, val: float): # TODO: could also set as int over max and make self._pitch a float (get will take in that max and return an int)
        self._proto.pitch = val

    # TODO: jazztribution.sample() or some variant -- see prev commits for comments

    def get_syllable(self) -> str:
        return self._proto.syllable

    def get_offset(self) -> float:
        return self._proto.offset

    def get_duration(self) -> float:
        return self._proto.duration

    def get_pitch(self) -> float:
        return self._proto.pitch

    def get_parent_word(self) -> WordProto:
        return self._proto.parent_word

    # TODO: return possible IPA representations (or pass into constructor the correct one)
    # TODO: return possible rhymes -- this gets to a SyllableGroup class which groups together syllables with these same methods -- just slightly diff implementation

    def valid(self):
        return isinstance(self._proto.offset, float) and 0 <= self._proto.offset < 1 # and others 

    def __repr__(self):
        return f"{self.get_syllable()} + (Offset {self.get_offset()} for {self.get_duration()} pitched at {self.get_pitch()})"

class Syllabifier(metaclass=abc.ABCMeta):
    def __init__(self, override=SyllableOverride(default_multi=GLOBAL_MULTI_OVERRIDE, default_single=GLOBAL_SINGLE_OVERRIDE)):
        self.multi_override = override.get_multi_override()
        self.single_override = override.get_single_override()

    @abc.abstractmethod
    def _syllabify(self, word):
        pass

    def _syllabify_override(self, word): # TODO: add return descriptors (e.g. Optional[Syllable] here)
        word = ALPHABET_REGEX('', word)
        if len(word) == 0:
            return []
        return self.multi_override.get(word) or ([word] if word in self.single_override else self._syllabify(word))

    def syllabify(self, line, _nltk=False, _rstrip=True, _generate=False) -> BarProto:
        # TODO: compare different options -- does _ntlk change behavior with/without rstrip? do some python -i testing
        if _rstrip:
            line = line.rstrip()
        line = line.replace("-", " ") # TODO: consider making this an option? might be fine to pass in dashes or nah if u change architecture - could be set in initializer with abstract class defaults ya know
        words = word_tokenize(line) if _nltk else line.split(" ") # optional split by dash and " " (or other symbols that are custom-defineable)
        
        bar_proto = BarProto()
        for idx, word in enumerate(words): # TODO: ntlk word tokenizer acts differently than simple split by " "
            word_proto = WordProto()
            word_proto.word = word
            word_proto.id = f"{idx}_{shortuuid.uuid()}" # this is probs fine for local use - might need to redesign later
            word_syllables = [Syllable.proto(s, word_proto) \
                                            for s in self._syllabify_override(word.lower()) \
                                                if s is not None] # check if passes a copy or nah, I guess we just care about the id and maybe str yeah
            word_proto.syllables.extend(word_syllables)
            
            bar_proto.syllables.extend(word_syllables)
            bar_proto.words.extend([word_proto])
            # TODO: maybe have override be optional... or can override the override dictionary with your own or an artist / song specific one? this might be part of metadata pbtxt
        
        return bar_proto

class SyllabifierNLTK(Syllabifier):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tokenizer = SyllableTokenizer()
        
    def _syllabify(self, word):
        return self.tokenizer.tokenize(word)

class SyllabifierHenchPy(Syllabifier):
    def __init__(self, backend=BACKEND_SONORITY, onset_text=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if backend == BACKEND_SONORITY:
            self.tokenize = SonoriPy
        elif backend == BACKEND_ONSET:
            assert onset_text is not None, "onset_text is None"
            self.tokenize = lambda word: LegaliPy(word, getOnsets(onset_text))
        else:
            raise Exception(f"Invalid HenchPy backend: {backend}")

    def _syllabify(self, word):
       return self.tokenize(word) 
