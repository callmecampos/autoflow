import abc
import abjad
from typing import Any, List, Optional, Union

import numpy as np

"""
NOTES:
Questions:
1. How to denote a triplet in general???
2. Should we have our own general note representation?
"""

class SheetMusicRenderer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def single_note(self, duration: float = "4", pitch: str = "c'"):
        """
        Render a single note of a pitch and duration denominator
        """
        pass

    @abc.abstractmethod
    def from_string(self, notes: str):
        pass

    #def __init__(self, bar_width_pix=100, bar_height_pix=25):
    #    self.render_width = bar_width_pix
    #    self.render_height = bar_height_pix
        # any other specifications required?

    @abc.abstractmethod
    def from_list(self, durations: List[float], pitches: List[str]):
        pass

"""
Notes:
- rendering notes might wanna wait until you have generalized tapping figured out
- problem: given a set of timings (impulses to start, but eventually rising and falling edges from key up / key down) generate a (discretized) symbolic musical notation from it
- for now: don't render notes, just render a pseudo renderer of syllables in bar format --> lyrical chart generator (likely on front end)
"""

class SheetMusicRendererAbjad(SheetMusicRenderer):
    def single_note(self, denominator: float = "4", pitch: str = "c'"):
        note = abjad.Note(pitch + f"{denominator}")
        abjad.show(note) # TODO: return as image / renderable type of some sort with specified dimensions in constructor --> still have abjad show -- just class allows for different functions... or just show image lol as validation

    def from_string(self, notes: Union[str, List[Any]]):
        voice = abjad.Voice(notes, name="RH_Voice")
        staff = abjad.Staff([voice], name="RH_Staff")
        score = abjad.Score([staff], name="Score")
        
        abjad.show(score) # again, have a better way of returning this as a renderable object (also have option to have abjad render it obviously -- instance variable that you can edit)

    # TODO: rendering a full bar (or all of sheet music? depends what's requested by the client -- lol server / client makes sense now)
    def from_list(self, denominators: List[float], pitches: Optional[List[str]] = None):
        if pitches is None:
            pitches = ["c'"] * len(denominators)
        notes = []
        for (denominator, pitch) in list(zip(denominators, pitches)):
            if ((np.log(denominator) / np.log(2)) % 1 == 0):
                notes.append(abjad.Note(f"{pitch}{denominator}"))
            elif (denominator % 3 == 0):
                notes.append(abjad.makers.tuplet_from_leaf_and_ratio(abjad.Note(f"{pitch}{int(denominator / 3)}"), 3 * [1]))

            # NOTE: there should maybe be a more general way to do this, talk to Xavi about this kind of auto-generation from discretized digital timings
            
            # TODO: have your own note representation maybe detached from any specific renderer and they have to map it to their internal representation (e.g. C up an octave == c'' in abjad... worth learning haha -- though I think for now we can just keep everything at c' and maybe a couple other simple pitches)
        
        print(notes)

        return self.from_string(notes)
    
"""
Only thing to change is being able to add lyrics below, which I'm sure Abjad & LilyPond can do

--

Current questions (Mon, May 2, 2022):
1. What is the best / most general digital representation of notes that can be easily converted from timings to rendered sheet music?
- See: (MIDI, PythonMusic)

Other questions (old):
1. What is the best way to auto-generate sheet music for rap that is accurate?
- Basic, annotate fourth beat stresses only and then evenly space the rest (for now --> then we can do more wild shit in between with *tapping*)
- Basic idea: beat stresses on fourths of 4x4 beat are one type of initial bowling bumper rails

Maybe --> phonetic syllable prior (options) auto-correlated to frequency domain of split audio signal --> interesting experiments would be to use clean audio signal

E.g.

"*Rap*pin like it's *auto*mated, *lights* I keep em *on* like Vegas"
"** Lava *ma*kin so *hot* I'm turnin *hog* to bacon"
"** only *God* could save him, ** I heard the *mon*sters made him"
"** I ain't a *star* I'm way *far*ther with the *con*stellations"

High Level: <-- THIS IS SUPER IMPORTANT LOL SORRY FOR ALL CAPS IK IT MAKES U FEEL LIKE WHOA CHILL BUT FR
- High Level Design Principle:
1. Make everything here modular (lyric generation, syllabic parsing (from lyrics *and* audio for informing and overrides), stress / pitch / musical annotation, BPM detection, other pattern recognition within the symbolic representation music) so that they can later be replaced with more complex less manual modules (ideally deep learning modules of sorts)

Eventually, two inputs should be (non-audio) 1. bars cat writes (audio) 2. bars cat spits live 3. lyrics cat recorded --> probably more naturally but KISS let it be easy haha

Maybe cracked out:
- Small style transfers (non-biting) or easy way to *tap out* or *speak out* flow straight from voice and play around with it and see why it sounds right
- Practice tool (bro u cracked)

Nice to Have: Test driven development
"""
