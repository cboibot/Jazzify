"""Register-limited, phrase-based solo generator."""
from .harmony import scale_for


def _pitch(pc, around, pitch_range):
    options = [pc + 12 * octave for octave in range(2, 8) if pitch_range[0] <= pc + 12 * octave <= pitch_range[1]]
    return min(options, key=lambda note: abs(note - around)) if options else max(pitch_range[0], min(pitch_range[1], around))


def generate_melody(chords, minor_key, profile, rng, instrument="Saxophone", bars=None, sections=None):
    bars = bars or len(chords)
    ranges = {"Saxophone": profile.sax_range, "Trumpet": profile.trumpet_range, "Guitar": profile.guitar_range}
    pitch_range = ranges[instrument]
    previous = pitch_range[0] + int((pitch_range[1] - pitch_range[0]) * (.30 if profile.low_register_bias > .6 else .5))
    events, motif = [], []
    section_starts = {start: name for name, start, _ in (sections or [])}
    for bar in range(bars):
        chord = chords[bar % len(chords)]
        section = next((name for name, start, length in (sections or []) if start <= bar < start + length), "THEME")
        # Dark arrangements keep the opening and ending sparse; development is permitted to speak more.
        activity = profile.solo_activity * (0.55 if section in ("INTRO", "OUTRO") else 1.0)
        if rng.random() > activity or (bar % profile.phrase_bars == profile.phrase_bars - 1 and rng.random() < profile.rest_chance):
            continue
        slots = (0, 1, 2, 3) if profile.density < .52 else (0,.5,1,1.5,2,2.5,3,3.5)
        phrase_end = bar % profile.phrase_bars == profile.phrase_bars - 1 or bar == bars - 1
        phrase_velocity = rng.randint(profile.velocity_low, profile.velocity_high)
        for index, beat in enumerate(slots):
            if rng.random() > profile.density or (index == 0 and rng.random() < profile.rest_chance): continue
            strong = beat in (0, 2)
            candidates = chord.tones if strong else scale_for(chord, minor_key)
            if motif and bar % (profile.phrase_bars * 2) == profile.phrase_bars and index < len(motif) and rng.random() < profile.repeat:
                pitch = motif[index]
            else:
                pc = rng.choice(candidates)
                direction = -1 if rng.random() < profile.descending_bias else 1
                step = rng.choice((0, 1, 2, 3, 5)) * direction
                if rng.random() < .08: step *= 2  # rare expressive leap
                pitch = _pitch(pc, previous + step, pitch_range)
                if not strong and rng.random() < profile.chromaticism: pitch = max(pitch_range[0], min(pitch_range[1], pitch + rng.choice((-1, 1))))
            if phrase_end and beat >= 2:
                pitch = _pitch(chord.tones[0], previous - 2 if profile.descending_bias > .5 else previous, pitch_range)
            duration = min(3.5 - beat, max(.3, profile.note_length * rng.choice((.7, 1, 1.35))))
            events.append((bar * 4 + beat, duration, pitch, max(25, min(110, phrase_velocity + rng.randint(-9, 9)))))
            previous = pitch
            if bar % (profile.phrase_bars * 2) == 0 and index < 3: motif.append(pitch)
    return events
