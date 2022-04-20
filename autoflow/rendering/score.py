import abc
import abjad
from typing import List

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

class SheetMusicRendererAbjad(SheetMusicRenderer):
    def single_note(self, duration: float = "4", pitch: str = "c'"):
        note = abjad.Note(pitch + duration)
        abjad.show(note) # TODO: return as image / renderable type of some sort with specified dimensions in constructor

    def from_string(self, notes: str):
        voice = abjad.Voice(notes, name="RH_Voice")
        staff = abjad.Staff([voice], name="RH_Staff")
        score = abjad.Score([staff], name="Score")
        
        abjad.show(score) # again, have a better way of returning this as a renderable object (also have option to have abjad render it obviously -- instance variable that you can edit)

    # TODO: rendering a full bar (or all of sheet music? depends what's requested by the client -- lol server / client makes sense now)
    def from_list(self, durations: List[float], pitches: List[str]):
        notes = ""
        for (dur, pitch) in list(zip(durations, pitches)):
            notes += f"{pitch}{duration} " # TODO: have your own note representation maybe detached from any specific renderer and they have to map it to their internal representation (e.g. C up an octave == c'' in abjad... worth learning haha -- though I think for now we can just keep everything at c' and maybe a couple other simple pitches)
        
        return self.from_string(notes)
