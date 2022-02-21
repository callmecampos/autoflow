class Bars:
    def __init__(self, verses, options={}):
        self.verses = verses
        self.options = options
        self.parse()

    @classmethod
    def load(cls, filepath):
        with open(filepath, "r") as f:
            return cls(f.readlines())

    def parse(self):
        pass # TODO: implement - loop through verses and build parsed_verses instance variable... what is a good representation for this?

"""
Questions:
Do syllables maybe map to general meter segments? (e.g. base + ... + 1/2^k)
Yes - can add some jazzy annotation if needed (random before / after -- maybe not just gaussian -- jazzian)

What is a useful UI for mapping syllabic repr. into words?
Tying (with line -- AutoLayout-esque) syllabic components to meter buckets (can further split or manually define if desired -- different ways of doing this)

Alignment of music to bar (or smaller units)?
Bar - MusixMatch API
Smaller units - custom? through UI? some basic manually set infra that let's us infer the rest -- we have already the words (some alignment) + the audio -- NLP that constrained bih
"""
