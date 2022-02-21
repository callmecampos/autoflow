# TODO: imports
import abc
from syllabipy.legalipy import LegaliPy, getOnsets

class Syllabifier(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def _syllabify(self, word):
        pass

    def syllabify(self, line):
        words = line.rstrip().split(" ") # optional split by dash and " " (or other symbols that are custom-defineable)
        for word in words:
            yield self.syllabify(word) # TODO: type this? should have standard of some sort -- see notes for discussion on this

