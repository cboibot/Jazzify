"""Chord vocabulary and mood-sensitive progression selection."""
from dataclasses import dataclass
import random

NOTE_NAMES = {"C":0,"C#":1,"Db":1,"D":2,"D#":3,"Eb":3,"E":4,"F":5,"F#":6,"Gb":6,"G":7,"G#":8,"Ab":8,"A":9,"A#":10,"Bb":10,"B":11}
QUALITY = {"maj7":(0,4,7,11),"m7":(0,3,7,10),"7":(0,4,7,10),"m7b5":(0,3,6,10),"dim7":(0,3,6,9),"m9":(0,3,7,10,14),"maj9":(0,4,7,11,14),"7b9":(0,4,7,10,13),"sus7":(0,5,7,10)}

@dataclass(frozen=True)
class Chord:
    root: int; quality: str; bars: int = 1
    @property
    def tones(self): return tuple((self.root + interval) % 12 for interval in QUALITY[self.quality])

def key_root(key: str) -> tuple[int, bool]:
    name, mode = key.rsplit(" ", 1); return NOTE_NAMES[name], mode.lower() == "minor"
def _chord(root, degree, quality): return Chord((root + degree) % 12, quality)

def progression(key: str, style: str, profile, rng: random.Random) -> list[Chord]:
    root, minor = key_root(key)
    dark = minor or profile.dark_harmony
    if style == "Blues":
        # A melancholy blues substitutes minor iv and a tense turnaround.
        pattern = (0,0,0,0,5,5,0,0,7,5,0,7) if not dark else (0,0,0,0,5,5,0,0,7,5,0,7)
        qualities = ["7"] * 12
        if dark: qualities[5], qualities[9], qualities[11] = "m7", "m7", "7b9"
        return [_chord(root, degree, quality) for degree, quality in zip(pattern, qualities)]
    if dark:
        choices = [[(0,"m9"),(10,"maj7"),(8,"maj7"),(7,"7b9"),(5,"m7"),(2,"m7b5"),(7,"7b9"),(0,"m9")], [(2,"m7b5"),(7,"7b9"),(0,"m9"),(10,"maj7"),(8,"maj7"),(5,"m7"),(2,"m7b5"),(7,"7b9")]]
    elif style == "Lo-fi Jazz":
        choices = [[(0,"maj7"),(9,"m7"),(2,"m7"),(7,"7"),(0,"maj7"),(9,"m7"),(2,"m7"),(7,"7")]]
    else:
        choices = [[(2,"m7"),(7,"7"),(0,"maj7"),(9,"m7"),(2,"m7"),(7,"7"),(0,"maj7"),(7,"7")],[(0,"maj7"),(9,"m7"),(2,"m7"),(7,"7"),(0,"maj7"),(5,"maj7"),(2,"m7"),(7,"7")]]
    result = [_chord(root, degree, quality) for degree, quality in rng.choice(choices)]
    if style == "Bebop": result[-1] = _chord(root, 7, "7b9")
    return result

def scale_for(chord: Chord, minor_key: bool) -> tuple[int, ...]:
    if chord.quality in ("7","7b9"): intervals = (0,2,4,5,7,9,10)
    elif chord.quality in ("m7","m9","m7b5") or minor_key: intervals = (0,2,3,5,7,8,10)
    else: intervals = (0,2,4,5,7,9,11)
    return tuple((chord.root + interval) % 12 for interval in intervals)
