"""Phrase and motif generation shared by all melodic arrangements."""
from dataclasses import dataclass
from .harmony import scale_for


@dataclass(frozen=True)
class MotifNote:
    offset: float
    duration: float
    pitch: int


def _nearest_pitch(pc, around, pitch_range):
    options = [pc + 12 * octave for octave in range(2, 8) if pitch_range[0] <= pc + 12 * octave <= pitch_range[1]]
    return min(options, key=lambda note: abs(note - around)) if options else max(pitch_range[0], min(pitch_range[1], around))


def motif_for(chord, minor_key, profile, rng, pitch_range):
    """Make one recognizable two-bar idea, later heard as A, A', B and A''."""
    dense = profile.density > .70
    offsets = (0,.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6) if dense else (0,1.1,2.4,4.0,5.2)
    if profile.density < .45: offsets = (0,1.5,3.6,5.2)
    around = pitch_range[0] + int((pitch_range[1] - pitch_range[0]) * (.32 if profile.low_register_bias > .5 else .5))
    notes = []
    for index, offset in enumerate(offsets):
        strong = offset % 2 < .12
        pc = rng.choice(chord.tones if strong else scale_for(chord, minor_key))
        direction = -1 if rng.random() < profile.descending_bias else 1
        step = direction * rng.choice((0,1,2,3,5))
        pitch = _nearest_pitch(pc, around + step, pitch_range)
        around = pitch
        duration = min(1.8, profile.note_length * (1.35 if index == len(offsets) - 1 else rng.choice((.7,1,1.15))))
        notes.append(MotifNote(offset, duration, pitch))
    return tuple(notes)


def _variant(motif, chord, profile, rng, pitch_range, kind):
    root_shift = ((chord.root - motif[0].pitch) % 12)
    if root_shift > 6: root_shift -= 12
    result = []
    for index, note in enumerate(motif):
        if kind == "B": shift = -root_shift if index % 2 else root_shift + rng.choice((-2,2))
        elif kind == "A''": shift = root_shift + (-12 if profile.low_register_bias > .55 and index % 3 == 0 else 0)
        else: shift = root_shift
        if kind == "A'" and index == len(motif) - 1:
            pitch = _nearest_pitch(chord.tones[0], note.pitch + shift, pitch_range)
        else:
            pitch = max(pitch_range[0], min(pitch_range[1], note.pitch + shift))
        # A' breathes slightly more; B breaks the rhythm while retaining the contour.
        offset = note.offset + (0.14 if kind == "B" and index % 2 else 0)
        duration = note.duration * (1.18 if kind == "A'" else .82 if kind == "B" else 1)
        result.append(MotifNote(offset, duration, pitch))
    return result


def section_gain(section):
    return {"INTRO":.62, "THEME":.80, "DEVELOPMENT":1.0, "SOLO":1.04, "RETURN":.84, "OUTRO":.55}[section]


def generate_melody(chords, minor_key, profile, rng, instrument="Saxophone", bars=None, sections=None, motif=None, solo_mode=False, entry_shift=0.0):
    """Render one shared idea in deliberately separated two-bar phrases."""
    bars = bars or len(chords)
    ranges = {"Piano": profile.piano_range, "Saxophone": profile.sax_range, "Trumpet": profile.trumpet_range, "Guitar": profile.guitar_range}
    pitch_range = ranges[instrument]
    motif = motif or motif_for(chords[0], minor_key, profile, rng, pitch_range)
    events, phrase_number = [], 0
    # Two-bar phrases make A / A' / B / A'' audible.  Sparse styles breathe
    # through activity and long notes, rather than disappearing for four bars.
    for start_bar in range(0, bars, 2):
        section = next(name for name, start, length in sections if start <= start_bar < start + length)
        if not solo_mode and section in ("INTRO", "OUTRO"): continue
        chance = 1.0 if solo_mode else profile.solo_activity
        if section in ("THEME", "RETURN"): chance = max(chance, .72)
        if rng.random() > chance: continue
        kind = ("A", "A'", "B", "A''")[phrase_number % 4]
        idea = _variant(motif, chords[start_bar % len(chords)], profile, rng, pitch_range, kind)
        phrase_velocity = int(rng.randint(profile.velocity_low, profile.velocity_high) * section_gain(section))
        for note in idea:
            absolute = start_bar * 4 + note.offset + entry_shift
            if absolute >= bars * 4: continue
            # Swing delays only offbeats; random variance stays small and phrase-aware.
            swing_delay = profile.swing * .16 if round(note.offset * 2) % 2 else 0
            timing = max(0, absolute + swing_delay + rng.uniform(-profile.humanize, profile.humanize))
            duration = max(.12, note.duration + rng.uniform(-profile.humanize, profile.humanize))
            events.append((timing, duration, note.pitch, max(24, min(112, phrase_velocity + rng.randint(-7,7)))))
        phrase_number += 1
    return events
