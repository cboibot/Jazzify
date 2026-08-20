"""Coordinates one coherent arrangement profile across all MIDI voices."""
from dataclasses import dataclass
from pathlib import Path
import random
from midiutil import MIDIFile
from .styles import profile_for
from .harmony import key_root, progression, QUALITY
from .melody import generate_melody
from .bass import generate_bass
from .drums import generate_drums

PROGRAMS = {"Piano":0, "Upright Bass":32, "Saxophone":65, "Trumpet":56, "Guitar":26}

@dataclass
class Composition:
    midi_path: Path; bpm: int; seconds: int; bars: int

def _add_events(midi, track, channel, events):
    # MIDIUtil pairs note-offs by pitch.  Prevent a repeated pitch from being
    # started before its earlier note has ended (common in dense bebop phrases).
    cleaned, active = [], {}
    for start, duration, pitch, velocity in sorted(events):
        if pitch in active:
            previous_index, previous_end = active[pitch]
            if start == cleaned[previous_index][0]:
                continue
            if start < previous_end:
                old_start, _, old_pitch, old_velocity = cleaned[previous_index]
                cleaned[previous_index] = (old_start, max(.05, start - old_start - .02), old_pitch, old_velocity)
        cleaned.append((start, duration, pitch, velocity))
        active[pitch] = (len(cleaned) - 1, start + duration)
    for start, duration, pitch, velocity in cleaned: midi.addNote(track, channel, pitch, start, duration, velocity)

def _section_plan(bars):
    if bars <= 12: plan = [("INTRO",2),("THEME",max(4,bars-4)),("OUTRO",2)]
    else:
        intro, outro = 2, 2; remaining = bars - intro - outro; theme = max(4, remaining // 3)
        plan = [("INTRO",intro),("THEME",theme),("DEVELOPMENT",max(4,remaining-theme*2)),("THEME VARIATION",theme),("OUTRO",outro)]
    start = 0; result = []
    for name, length in plan: result.append((name,start,length)); start += length
    return result

def _section_at(sections, bar): return next(name for name,start,length in sections if start <= bar < start + length)

def _piano_events(chords, profile, rng, bars, sections):
    events = []
    for bar in range(bars):
        section = _section_at(sections, bar)
        if rng.random() > profile.piano_activity * (.65 if section == "INTRO" else 1): continue
        chord = chords[bar % len(chords)]
        # Dark/ballad profiles use wide, low sustained voicings and fewer attacks.
        sparse = profile.low_register_bias > .6 or profile.density < .45
        beats = [0] if sparse else ([0,2] if rng.random() < profile.syncopation else [0,1.5,3])
        for beat in beats:
            root = chord.root + (36 if profile.low_register_bias > .55 else 43) + rng.choice((0,12))
            intervals = QUALITY[chord.quality]
            upper = [root + interval for interval in intervals[1:]]
            if profile.dark_harmony: upper = [note + (12 if index > 0 else 0) for index, note in enumerate(upper)]
            voicing = sorted({root} | {max(profile.piano_range[0], min(profile.piano_range[1], note)) for note in upper})
            duration = min(3.7 - beat, profile.note_length * (1.55 if sparse else rng.choice((.8,1.1,1.4))))
            velocity_ceiling = profile.velocity_high - (12 if section in ("INTRO","OUTRO") else 0)
            for pitch in voicing: events.append((bar*4+beat, duration, pitch, rng.randint(profile.velocity_low, max(profile.velocity_low, velocity_ceiling))))
    return events

def create_composition(settings: dict, output_dir: Path) -> Composition:
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random()
    profile = profile_for(settings["style"], settings["mood"])
    # User BPM remains the central choice, while profile supplies an audible stylistic pull.
    bpm = max(35, min(300, round(int(settings["bpm"]) * profile.tempo_scale)))
    requested = int(settings["duration"]); bars = max(4, round(requested * bpm / 240)); seconds = round(bars * 240 / bpm)
    _, minor_key = key_root(settings["key"])
    chords = progression(settings["key"], settings["style"], profile, rng)
    sections = _section_plan(bars); selected = settings["instruments"]
    tracks = 1 + len([name for name in selected if name != "Drums"])
    # Events are already sanitized in _add_events; disable MIDIUtil's fragile
    # reordering pass, which can mis-pair repeated notes in dense solo lines.
    midi = MIDIFile(tracks, adjust_origin=False, deinterleave=False); midi.addTempo(0, 0, bpm)
    track, channel = 0, 0
    if "Piano" in selected:
        midi.addProgramChange(track,channel,0,PROGRAMS["Piano"]); _add_events(midi,track,channel,_piano_events(chords,profile,rng,bars,sections)); track += 1; channel += 1
    if "Upright Bass" in selected:
        midi.addProgramChange(track,channel,0,PROGRAMS["Upright Bass"]); _add_events(midi,track,channel,generate_bass(chords,minor_key,profile,rng,bars,sections)); track += 1; channel += 1
    if "Drums" in selected: _add_events(midi,0,9,generate_drums(profile,rng,bars,[start for _,start,_ in sections]))
    for instrument in ("Saxophone","Trumpet","Guitar"):
        if instrument in selected:
            midi.addProgramChange(track,channel,0,PROGRAMS[instrument])
            # Optional brass is deliberately sparse in dark arrangements.
            if instrument != "Trumpet" or rng.random() < (1 - profile.low_register_bias * .72):
                _add_events(midi,track,channel,generate_melody(chords,minor_key,profile,rng,instrument,bars,sections))
            track += 1; channel += 1
    midi_path = output_dir / "jazzify_latest.mid"
    with midi_path.open("wb") as stream: midi.writeFile(stream)
    return Composition(midi_path,bpm,seconds,bars)
