from .harmony import scale_for

def generate_bass(chords, minor_key, profile, rng, bars, sections=None):
    events, previous = [], profile.bass_range[0] + 10
    for bar in range(bars):
        chord = chords[bar % len(chords)]
        section = next((name for name, start, length in (sections or []) if start <= bar < start + length), "THEME")
        if rng.random() > profile.bass_activity: continue
        walking = profile.walking_bass > .62 and section != "INTRO"
        positions = (0,1,2,3) if walking else (0,2)
        for index, beat in enumerate(positions):
            if index == 0: pc = chord.root
            elif index == len(positions) - 1 and bar + 1 < bars: pc = (chords[(bar + 1) % len(chords)].root + rng.choice((-1,1))) % 12
            else: pc = rng.choice(chord.tones if rng.random() < .72 else scale_for(chord, minor_key))
            choices = [pc + 12 * octave for octave in range(1, 5) if profile.bass_range[0] <= pc + 12 * octave <= profile.bass_range[1]]
            pitch = min(choices, key=lambda note: abs(note - previous))
            duration = .78 if walking else min(2.6, 1.4 * profile.note_length)
            events.append((bar * 4 + beat, duration, pitch, rng.randint(profile.velocity_low + 8, profile.velocity_high)))
            previous = pitch
    return events
