import shutil
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from generator.composition import create_composition
from audio.midi_renderer import AudioSetupError, render_midi
from audio.playback import play_wav, stop

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
INSTRUMENTS = ("Piano", "Upright Bass", "Drums", "Saxophone", "Trumpet", "Guitar")
KEYS = ("C Major", "D Minor", "Eb Major", "F Minor", "G Major", "A Minor", "Bb Major")
DURATIONS = {"30 seconds": 30, "60 seconds": 60, "90 seconds": 90, "2 minutes": 120, "3 minutes": 180, "5 minutes": 300}


class JazzifyApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Jazzify — Procedural Jazz Generator")
        self.root.geometry("590x700")
        self.root.minsize(520, 650)
        self.wav_path = None
        self.instrument_vars = {name: tk.BooleanVar(value=name in ("Piano", "Upright Bass", "Drums", "Saxophone")) for name in INSTRUMENTS}
        self.style = tk.StringVar(value="Jazz")
        self.mood = tk.StringVar(value="Dark")
        self.key = tk.StringVar(value="D Minor")
        self.bpm = tk.StringVar(value="80")
        self.duration = tk.StringVar(value="60 seconds")
        self.status = tk.StringVar(value="Ready")
        self._build()

    def _build(self):
        frame = ttk.Frame(self.root, padding=22)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="JAZZIFY", font=("Segoe UI", 25, "bold")).pack(pady=(0, 20))
        ttk.Label(frame, text="INSTRUMENTS", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        check_area = ttk.Frame(frame); check_area.pack(fill="x", pady=(5, 16))
        for index, name in enumerate(INSTRUMENTS):
            ttk.Checkbutton(check_area, text=name, variable=self.instrument_vars[name]).grid(row=index // 2, column=index % 2, sticky="w", padx=(0, 90), pady=2)
        fields = (("STYLE", self.style, ("Jazz", "Blues", "Dark Jazz", "Lo-fi Jazz", "Bebop", "Jazz Ballad")),
                  ("MOOD", self.mood, ("Dark", "Melancholic", "Relaxed", "Mysterious", "Energetic", "Dreamy")),
                  ("KEY", self.key, KEYS), ("BPM", self.bpm, None), ("DURATION", self.duration, tuple(DURATIONS)))
        for label, variable, choices in fields:
            ttk.Label(frame, text=label, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(4, 2))
            if choices:
                ttk.Combobox(frame, textvariable=variable, values=choices, state="readonly", width=28).pack(anchor="w")
            else:
                ttk.Entry(frame, textvariable=variable, width=12).pack(anchor="w")
        self.generate_button = ttk.Button(frame, text="GENERATE", command=self.generate)
        self.generate_button.pack(pady=20)
        ttk.Separator(frame).pack(fill="x", pady=8)
        ttk.Label(frame, text="Generated composition", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(8, 3))
        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.pack(fill="x", pady=(0, 10))
        controls = ttk.Frame(frame); controls.pack(anchor="w")
        self.play_button = ttk.Button(controls, text="PLAY", command=self.play, state="disabled"); self.play_button.grid(row=0, column=0, padx=(0, 7))
        ttk.Button(controls, text="STOP", command=stop).grid(row=0, column=1, padx=7)
        self.save_button = ttk.Button(controls, text="SAVE AUDIO", command=self.save_audio, state="disabled"); self.save_button.grid(row=0, column=2, padx=7)
        ttk.Label(frame, textvariable=self.status, foreground="#555").pack(anchor="w", pady=(13, 0))

    def generate(self):
        selected = [name for name, variable in self.instrument_vars.items() if variable.get()]
        try:
            bpm = int(self.bpm.get())
            if not 35 <= bpm <= 300: raise ValueError
            if not selected: raise ValueError("Select at least one instrument.")
        except ValueError as error:
            messagebox.showerror("Invalid settings", str(error) if str(error) else "BPM must be between 35 and 300.")
            return
        settings = dict(instruments=selected, style=self.style.get(), mood=self.mood.get(), key=self.key.get(), bpm=bpm, duration=DURATIONS[self.duration.get()])
        self.generate_button.configure(state="disabled"); self.progress.start(12); self.status.set("Composing MIDI and rendering audio…")
        threading.Thread(target=self._generate_worker, args=(settings,), daemon=True).start()

    def _generate_worker(self, settings):
        try:
            composition = create_composition(settings, OUTPUT)
            wav = render_midi(composition.midi_path, OUTPUT / "jazzify_latest.wav")
            self.root.after(0, self._generation_complete, wav, f"Ready — {composition.bars} bars, about {composition.seconds} seconds.")
        except (AudioSetupError, Exception) as error:
            self.root.after(0, self._generation_failed, str(error))

    def _generation_complete(self, wav, text):
        self.wav_path = wav; self.progress.stop(); self.generate_button.configure(state="normal")
        self.play_button.configure(state="normal"); self.save_button.configure(state="normal"); self.status.set(text)

    def _generation_failed(self, error):
        self.progress.stop(); self.generate_button.configure(state="normal"); self.status.set("Generation failed")
        messagebox.showerror("Jazzify could not render audio", error)

    def play(self):
        if self.wav_path: play_wav(self.wav_path)

    def save_audio(self):
        if not self.wav_path: return
        destination = filedialog.asksaveasfilename(title="Save generated audio", defaultextension=".wav", filetypes=[("WAV audio", "*.wav")])
        if destination:
            shutil.copy2(self.wav_path, destination); self.status.set(f"Saved audio to {destination}")

    def run(self):
        self.root.mainloop()
