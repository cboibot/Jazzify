"""Build section-aware ensemble or solo arrangements from one shared musical idea."""
from dataclasses import dataclass
from pathlib import Path
import random
from midiutil import MIDIFile
from .styles import profile_for
from .harmony import key_root, progression, QUALITY
from .melody import generate_melody, motif_for, section_gain
from .bass import generate_bass
from .drums import generate_drums

PROGRAMS = {"Piano":0, "Upright Bass":32, "Saxophone":65, "Trumpet":56, "Guitar":26}

@dataclass
class Composition:
    midi_path: Path
    bpm: int
    seconds: int
    bars: int


def _add_events(midi, track, channel, events):
    """Avoid MIDIUtil's same-pitch note-pairing issue after humanization."""
    cleaned, active = [], {}
    for start, duration, pitch, velocity in sorted(events):
        if pitch in active:
            prior, prior_end = active[pitch]
            prior_start = cleaned[prior][0]
            if abs(start - prior_start) < .01:
                continue
            if start < prior_end:
                _, _, old_pitch, old_velocity = cleaned[prior]
                cleaned[prior] = (prior_start, max(.06, start - prior_start - .015), old_pitch, old_velocity)
        cleaned.append((start, duration, pitch, velocity))
        active[pitch] = (len(cleaned) - 1, start + duration)
    for start, duration, pitch, velocity in cleaned:
        midi.addNote(track, channel, pitch, start, duration, velocity)


def _section_plan(bars):
    if bars <= 8:
        plan = [("INTRO",1),("THEME",max(3,bars-3)),("OUTRO",2)]
    elif bars <= 20:
        middle = bars - 4; theme = max(2, middle // 3); development = max(2, middle - theme * 2)
        plan = [("INTRO",2),("THEME",theme),("DEVELOPMENT",development),("RETURN",theme),("OUTRO",2)]
    else:
        middle = bars - 4; theme = max(4, middle // 4); development = max(3, (middle - theme * 2) // 2)
        solo = middle - theme * 2 - development * 2
        plan = [("INTRO",2),("THEME",theme),("DEVELOPMENT",development),("SOLO",max(3,solo)),("DEVELOPMENT",development),("RETURN",theme),("OUTRO",2)]
    start, result = 0, []
    for name, length in plan:
        result.append((name,start,length)); start += length
    return result


def _section_at(sections, bar):
    return next(name for name, start, length in sections if start <= bar < start + length)


def _comp_events(chords, profile, rng, bars, sections, instrument="Piano", solo_mode=False):
    pitch_range = profile.piano_range if instrument == "Piano" else profile.guitar_range
    activity = profile.piano_activity if instrument == "Piano" else profile.piano_activity * .82
    events = []
    for bar in range(bars):
        section = _section_at(sections, bar)
        if not solo_mode and section == "OUTRO" and rng.random() > .55: continue
        if rng.random() > (1.0 if solo_mode else activity * (.70 if section == "INTRO" else 1)): continue
        chord = chords[bar % len(chords)]
        sparse = profile.low_register_bias > .55 or profile.density < .45
        beats = (0,) if sparse else ((0,2) if rng.random() < profile.syncopation else (0,1.5,3))
        for beat in beats:
            base = chord.root + (36 if instrument == "Piano" and profile.low_register_bias > .5 else 43 if instrument == "Piano" else 48)
            intervals = QUALITY[chord.quality]
            upper = [base + interval for interval in intervals[1:]]
            if profile.dark_harmony: upper = [note + (12 if index > 0 else 0) for index, note in enumerate(upper)]
            voicing = sorted({base} | {max(pitch_range[0], min(pitch_range[1], note)) for note in upper})
            duration = min(3.7-beat, profile.note_length * (1.55 if sparse else rng.choice((.8,1.1,1.4))))
            time = bar * 4 + beat + rng.uniform(-profile.humanize, profile.humanize)
            ceiling = profile.velocity_high - (12 if section in ("INTRO","OUTRO") else 0)
            for pitch in voicing:
                events.append((max(0,time), max(.2,duration), pitch, max(25,int(rng.randint(profile.velocity_low,ceiling) * section_gain(section)))))
    return events


def _ending(chord, profile, instrument, end_time):
    ranges = {"Piano":profile.piano_range,"Upright Bass":profile.bass_range,"Saxophone":profile.sax_range,"Trumpet":profile.trumpet_range,"Guitar":profile.guitar_range}
    low, high = ranges[instrument]
    root = min((chord.root + 12 * octave for octave in range(2,7) if low <= chord.root + 12 * octave <= high), key=lambda note: abs(note - (low + high) // 2))
    if instrument == "Piano":
        return [(end_time,1.8,max(low,root-12),38),(end_time,1.8,root,44),(end_time,1.8,min(high,root+7),42)]
    return [(end_time,1.7,root,max(28,profile.velocity_low))]


def create_composition(settings: dict, output_dir: Path) -> Composition:
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random()
    profile = profile_for(settings["style"], settings["mood"])
    # The UI applies a style's automatic BPM, but a manual BPM is an exact override.
    bpm = max(35, min(300, int(settings["bpm"])))
    requested = int(settings["duration"])
    bars = max(4, round(requested * bpm / 240)); seconds = round(bars * 240 / bpm)
    _, minor_key = key_root(settings["key"])
    chords = progression(settings["key"], settings["style"], profile, rng)
    sections, selected = _section_plan(bars), settings["instruments"]
    solo_mode = len(selected) == 1
    lead = next((name for name in ("Saxophone","Trumpet","Guitar","Piano") if name in selected), "Saxophone")
    lead_range = {"Piano":profile.piano_range,"Saxophone":profile.sax_range,"Trumpet":profile.trumpet_range,"Guitar":profile.guitar_range}[lead]
    shared_motif = motif_for(chords[0], minor_key, profile, rng, lead_range)

    tracks = 1 + len([name for name in selected if name != "Drums"])
    midi = MIDIFile(tracks, adjust_origin=False, deinterleave=False)
    midi.addTempo(0, 0, bpm)
    track, channel, end_time = 0, 0, bars * 4 - 2

    if "Piano" in selected:
        midi.addProgramChange(track, channel, 0, PROGRAMS["Piano"])
        events = _comp_events(chords, profile, rng, bars, sections, "Piano", solo_mode)
        if solo_mode:
            # A solo pianist supplies left-hand motion and the shared upper-voice theme.
            events += generate_bass(chords, minor_key, profile, rng, bars, sections, solo_mode=True)
            events += generate_melody(chords, minor_key, profile, rng, "Piano", bars, sections, shared_motif, solo_mode=True)
        elif any(name in selected for name in ("Saxophone","Trumpet","Guitar")):
            # Piano answers the lead only after its phrase, leaving a tangible breath.
            events += generate_melody(chords, minor_key, profile, rng, "Piano", bars, sections, shared_motif, entry_shift=6.25)
        events += _ending(chords[-1], profile, "Piano", end_time)
        _add_events(midi, track, channel, events); track += 1; channel += 1

    if "Upright Bass" in selected:
        midi.addProgramChange(track, channel, 0, PROGRAMS["Upright Bass"])
        events = generate_bass(chords, minor_key, profile, rng, bars, sections, solo_mode=solo_mode)
        events += _ending(chords[-1], profile, "Upright Bass", end_time)
        _add_events(midi, track, channel, events); track += 1; channel += 1

    if "Drums" in selected:
        _add_events(midi, 0, 9, generate_drums(profile, rng, bars, sections, solo_mode=solo_mode))

    for instrument in ("Saxophone","Trumpet","Guitar"):
        if instrument not in selected: continue
        midi.addProgramChange(track, channel, 0, PROGRAMS[instrument])
        events = generate_melody(chords, minor_key, profile, rng, instrument, bars, sections, shared_motif, solo_mode=solo_mode)
        if instrument == "Guitar" and solo_mode:
            events += _comp_events(chords, profile, rng, bars, sections, "Guitar", solo_mode=True)
        events += _ending(chords[-1], profile, instrument, end_time)
        _add_events(midi, track, channel, events); track += 1; channel += 1

    midi_path = output_dir / "jazzify_latest.mid"
    with midi_path.open("wb") as stream:
        midi.writeFile(stream)
    return Composition(midi_path, bpm, seconds, bars)
