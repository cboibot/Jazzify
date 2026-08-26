"""Render MIDI to WAV with FluidSynth's command-line executable."""
from pathlib import Path
import os, shutil, subprocess


class AudioSetupError(RuntimeError):
    pass


def find_fluidsynth() -> str | None:
    configured = os.getenv("FLUIDSYNTH_PATH")
    bundled = Path(__file__).resolve().parents[1] / "tools" / "fluidsynth" / "bin" / "fluidsynth.exe"
    if configured and Path(configured).exists():
        return configured
    return str(bundled) if bundled.exists() else shutil.which("fluidsynth")


def find_soundfont() -> Path | None:
    configured = os.getenv("JAZZIFY_SOUNDFONT")
    candidates = [Path(configured)] if configured else []
    assets = Path(__file__).resolve().parents[1] / "assets"
    candidates += [assets / "FluidR3_GM.sf2", assets / "GeneralUser-GS.sf2", assets / "MuseScore_General.sf3",
                   Path(r"C:\\Program Files\\FluidSynth\\soundfonts\\FluidR3_GM.sf2")]
    return next((path.resolve() for path in candidates if path.exists()), None)


def render_midi(midi_path: Path, wav_path: Path) -> Path:
    executable, soundfont = find_fluidsynth(), find_soundfont()
    if not executable:
        raise AudioSetupError("FluidSynth was not found. Set FLUIDSYNTH_PATH to fluidsynth.exe.")
    if not soundfont:
        raise AudioSetupError("No SoundFont found. Download one and set JAZZIFY_SOUNDFONT to its .sf2 path.")
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    # -T is essential: FluidSynth otherwise fast-renders raw PCM despite the .wav suffix.
    command = [executable, "-ni", "-T", "wav", "-r", "44100", "-F", str(wav_path), str(soundfont), str(midi_path)]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
    except OSError as error:
        raise AudioSetupError(f"Could not start FluidSynth: {error}") from error
    # A tiny WAV is FluidSynth's error placeholder, not playable music.
    if result.returncode != 0 or not wav_path.exists() or wav_path.stat().st_size < 44100:
        detail = (result.stderr or result.stdout).strip()
        raise AudioSetupError(f"FluidSynth could not render the WAV. {detail}")
    return wav_path
