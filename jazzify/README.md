# Jazzify

Jazzify is a small desktop procedural-jazz prototype. It turns selected instruments, style, mood, key, tempo and duration into constrained composition data, writes a MIDI file with MIDIUtil, and renders that file to WAV with FluidSynth and a General MIDI SoundFont.

## Run

Use a working Python 3.11–3.14 installation (the checked-in virtual environment points at a Python installation that is currently missing on this machine):

```powershell
cd C:\Users\lenovo\Documents\ChatGPT\jazzify\jazzify
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Install FluidSynth for Windows and download a General MIDI `.sf2` SoundFont such as FluidR3_GM. Then configure them for the current shell:

```powershell
$env:FLUIDSYNTH_PATH = 'C:\path\to\fluidsynth.exe'
$env:JAZZIFY_SOUNDFONT = 'C:\path\to\FluidR3_GM.sf2'
python main.py
```

Alternatively put a SoundFont at `assets\FluidR3_GM.sf2`, `assets\GeneralUser-GS.sf2`, or `assets\MuseScore_General.sf3`; a locally unpacked `tools\fluidsynth\bin\fluidsynth.exe` is detected automatically.

## Generation

The generator selects an appropriate ii–V–I, minor, turnaround, or 12-bar blues progression. Piano voicings, bass movement, melody/solo lines and jazz drums all receive the same chord sequence. Each style-and-mood pair also has a shared arrangement profile: it changes tempo pull, harmony vocabulary, register limits, phrase rests, note lengths, dynamics, instrument activity, contour, and section entrances. Dark and melancholic profiles use lower/sparser arrangements and descending sustained phrases; bebop is higher, denser and more chromatic.

Supported styles are Jazz, Blues, Dark Jazz, Lo-fi Jazz, Bebop and Jazz Ballad. Choosing a style automatically fills in its recommended key and BPM, and displays density, velocity and swing defaults. Editing key or BPM marks it as a user override; selecting another style or using **Reset Style Defaults** restores automatic values. Moods then modify the style rather than replacing it. Available instruments are piano, upright bass, drums, saxophone, trumpet and guitar.

The composition engine organizes melodic material as recurring A, A', B and A'' motif phrases. Ensemble instruments share that idea, harmony and section plan, while piano can respond after a lead phrase. A single selected instrument receives a dedicated solo arrangement: piano adds left-hand motion and an upper voice, guitar alternates comping and melody, solo horns phrase with space, bass shapes walking phrases, and drums use form changes and fills.

## Output and limitations

Each successful generation creates `output\jazzify_latest.mid` and `output\jazzify_latest.wav`; the GUI plays the WAV with Windows' native audio subsystem and can copy it anywhere. Audio quality depends on the selected SoundFont. This intentional prototype uses General MIDI instruments and simple generated accompaniment rather than expressive performance data or live audio input.
