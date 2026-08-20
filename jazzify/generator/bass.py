"""Bass establishes the pulse and closes phrases instead of filling every bar."""
from .harmony import scale_for
from .melody import section_gain


def generate_bass(chords, minor_key, profile, rng, bars, sections=None, solo_mode=False):
    events, previous = [], profile.bass_range[0] + 10
    for bar in range(bars):
        section = next(name for name, start, length in sections if start <= bar < start + length)
        activity = 1.0 if solo_mode else profile.bass_activity
        if rng.random() > activity * (.64 if section == "OUTRO" else 1): continue
        chord = chords[bar % len(chords)]
        walking = profile.walking_bass > .62 and section not in ("INTRO", "OUTRO")
        positions = (0,1,2,3) if walking else (0,2)
        if solo_mode and bar % profile.phrase_bars == profile.phrase_bars - 1: positions = (0,)
        for index, beat in enumerate(positions):
            if index == 0: pc = chord.root
            elif index == len(positions) - 1 and bar + 1 < bars: pc = (chords[(bar + 1) % len(chords)].root + rng.choice((-1,1))) % 12
            else: pc = rng.choice(chord.tones if rng.random() < .72 else scale_for(chord, minor_key))
            choices = [pc + 12 * octave for octave in range(1,5) if profile.bass_range[0] <= pc + 12 * octave <= profile.bass_range[1]]
            pitch = min(choices, key=lambda note: abs(note - previous))
            time = bar * 4 + beat + rng.uniform(-profile.humanize, profile.humanize)
            duration = (.78 if walking else min(2.7, 1.4 * profile.note_length)) + rng.uniform(-profile.humanize, profile.humanize)
            velocity = int(rng.randint(profile.velocity_low + 7, profile.velocity_high) * section_gain(section))
            events.append((max(0,time), max(.15,duration), pitch, max(24,velocity)))
            previous = pitch
    return events
