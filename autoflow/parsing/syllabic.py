# TODO: imports
import abc
from nltk import word_tokenize
from nltk.tokenize import SyllableTokenizer
# TODO: try except in case not installed
from syllabipy.legalipy import LegaliPy, getOnsets
from syllabipy.sonoripy import SonoriPy

BACKEND_SONORITY = "sonoripy"
BACKEND_ONSET = "legalipy"

class Syllabifier(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def _syllabify(self, word):
        pass

    def syllabify(self, line, _nltk=False, _rstrip=True, _generate=False): # TODO: compare different options -- does _ntlk change behavior with/without rstrip? do some python -i testing
        if _rstrip:
            line = line.rstrip()
        words = word_tokenize(line) if _nltk else line.split(" ") # optional split by dash and " " (or other symbols that are custom-defineable)
        syllable_pack = []
        for word in words: # TODO: ntlk word tokenizer acts differently than simple split by " "
            syllable_pack.append(self._syllabify(word))
        
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
