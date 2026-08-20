import shutil
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from generator.composition import create_composition
from generator.styles import style_defaults
from audio.midi_renderer import AudioSetupError, render_midi
from audio.playback import play_wav, stop

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
INSTRUMENTS = ("Piano", "Upright Bass", "Drums", "Saxophone", "Trumpet", "Guitar")
KEYS = ("C Major", "D Minor", "Eb Major", "F Minor", "G Major", "A Minor", "Bb Major")
DURATIONS = {"30 seconds":30, "60 seconds":60, "90 seconds":90, "2 minutes":120, "3 minutes":180, "5 minutes":300}
STYLES = ("Jazz", "Blues", "Dark Jazz", "Lo-fi Jazz", "Bebop", "Jazz Ballad")
MOODS = ("Dark", "Melancholic", "Relaxed", "Mysterious", "Energetic", "Dreamy")


class JazzifyApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Jazzify — Procedural Jazz Generator")
        self.root.geometry("610x795")
        self.root.minsize(540, 720)
        self.wav_path, self._applying_defaults, self.overrides = None, False, set()
        self.instrument_vars = {name: tk.BooleanVar(value=name in ("Piano","Upright Bass","Drums","Saxophone")) for name in INSTRUMENTS}
        self.style, self.mood = tk.StringVar(value="Jazz"), tk.StringVar(value="Dark")
        self.key, self.bpm, self.duration = tk.StringVar(), tk.StringVar(), tk.StringVar(value="60 seconds")
        self.key_state, self.bpm_state = tk.StringVar(), tk.StringVar()
        self.profile_text, self.status = tk.StringVar(), tk.StringVar(value="Ready")
        self._build()
        self.style.trace_add("write", self._style_changed)
        self.key.trace_add("write", lambda *_: self._mark_override("key"))
        self.bpm.trace_add("write", lambda *_: self._mark_override("bpm"))
        self._apply_style_defaults()

    def _build(self):
        frame = ttk.Frame(self.root, padding=22); frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="JAZZIFY", font=("Segoe UI",25,"bold")).pack(pady=(0,16))
        ttk.Label(frame, text="INSTRUMENTS", font=("Segoe UI",10,"bold")).pack(anchor="w")
        choices = ttk.Frame(frame); choices.pack(fill="x", pady=(5,12))
        for index, name in enumerate(INSTRUMENTS):
            ttk.Checkbutton(choices,text=name,variable=self.instrument_vars[name]).grid(row=index//2,column=index%2,sticky="w",padx=(0,90),pady=2)
        self._combo_field(frame, "STYLE", self.style, STYLES)
        self._combo_field(frame, "MOOD", self.mood, MOODS)
        self._combo_field(frame, "KEY", self.key, KEYS)
        ttk.Label(frame, textvariable=self.key_state, foreground="#557" ).pack(anchor="w")
        ttk.Label(frame, text="BPM", font=("Segoe UI",9,"bold")).pack(anchor="w",pady=(4,2))
        ttk.Entry(frame,textvariable=self.bpm,width=12).pack(anchor="w")
        ttk.Label(frame,textvariable=self.bpm_state,foreground="#557").pack(anchor="w")
        self._combo_field(frame, "DURATION", self.duration, tuple(DURATIONS))
        ttk.Label(frame,text="ARRANGEMENT PROFILE",font=("Segoe UI",9,"bold")).pack(anchor="w",pady=(9,2))
        ttk.Label(frame,textvariable=self.profile_text,foreground="#445",wraplength=540,justify="left").pack(anchor="w")
        ttk.Button(frame,text="RESET STYLE DEFAULTS",command=self._apply_style_defaults).pack(anchor="w",pady=(5,5))
        ttk.Label(frame,text="Changing style restores its automatic key and BPM. Editing key or BPM marks it as a user override.",foreground="#666",wraplength=540,justify="left").pack(anchor="w")
        self.generate_button = ttk.Button(frame,text="GENERATE",command=self.generate); self.generate_button.pack(pady=14)
        ttk.Separator(frame).pack(fill="x",pady=7)
        ttk.Label(frame,text="Generated composition",font=("Segoe UI",11,"bold")).pack(anchor="w",pady=(7,3))
        self.progress = ttk.Progressbar(frame,mode="indeterminate"); self.progress.pack(fill="x",pady=(0,9))
        controls = ttk.Frame(frame); controls.pack(anchor="w")
        self.play_button = ttk.Button(controls,text="PLAY",command=self.play,state="disabled"); self.play_button.grid(row=0,column=0,padx=(0,7))
        ttk.Button(controls,text="STOP",command=stop).grid(row=0,column=1,padx=7)
        self.save_button = ttk.Button(controls,text="SAVE AUDIO",command=self.save_audio,state="disabled"); self.save_button.grid(row=0,column=2,padx=7)
        ttk.Label(frame,textvariable=self.status,foreground="#555").pack(anchor="w",pady=(12,0))

    def _combo_field(self, parent, label, variable, values):
        ttk.Label(parent,text=label,font=("Segoe UI",9,"bold")).pack(anchor="w",pady=(4,2))
        ttk.Combobox(parent,textvariable=variable,values=values,state="readonly",width=28).pack(anchor="w")

    def _style_changed(self, *_):
        if not self._applying_defaults: self._apply_style_defaults()

    def _mark_override(self, name):
        if self._applying_defaults: return
        self.overrides.add(name)
        self._refresh_default_labels()

    def _apply_style_defaults(self):
        defaults = style_defaults(self.style.get())
        self._applying_defaults = True
        self.overrides.clear(); self.key.set(defaults.key); self.bpm.set(str(defaults.bpm))
        self._applying_defaults = False
        self._refresh_default_labels()

    def _refresh_default_labels(self):
        defaults = style_defaults(self.style.get())
        self.key_state.set("User override" if "key" in self.overrides else "Automatic: selected by style")
        self.bpm_state.set("User override" if "bpm" in self.overrides else "Automatic: selected by style")
        self.profile_text.set(f"Automatic — Density: {defaults.density_label}   •   Velocity: {defaults.velocity_label}   •   Swing: {defaults.swing_label}")

    def generate(self):
        selected = [name for name, variable in self.instrument_vars.items() if variable.get()]
        try:
            bpm = int(self.bpm.get())
            if not 35 <= bpm <= 300: raise ValueError
            if not selected: raise ValueError("Select at least one instrument.")
        except ValueError as error:
            messagebox.showerror("Invalid settings",str(error) if str(error) else "BPM must be between 35 and 300.")
            return
        settings = dict(instruments=selected,style=self.style.get(),mood=self.mood.get(),key=self.key.get(),bpm=bpm,duration=DURATIONS[self.duration.get()])
        self.generate_button.configure(state="disabled"); self.progress.start(12); self.status.set("Composing phrases and rendering audio…")
        threading.Thread(target=self._generate_worker,args=(settings,),daemon=True).start()

    def _generate_worker(self, settings):
        try:
            composition = create_composition(settings,OUTPUT)
            wav = render_midi(composition.midi_path,OUTPUT / "jazzify_latest.wav")
            self.root.after(0,self._generation_complete,wav,f"Ready — {composition.bars} bars, about {composition.seconds} seconds.")
        except (AudioSetupError,Exception) as error:
            self.root.after(0,self._generation_failed,str(error))

    def _generation_complete(self,wav,text):
        self.wav_path = wav; self.progress.stop(); self.generate_button.configure(state="normal")
        self.play_button.configure(state="normal"); self.save_button.configure(state="normal"); self.status.set(text)

    def _generation_failed(self,error):
        self.progress.stop(); self.generate_button.configure(state="normal"); self.status.set("Generation failed")
        messagebox.showerror("Jazzify could not render audio",error)

    def play(self):
        if self.wav_path: play_wav(self.wav_path)

    def save_audio(self):
        if not self.wav_path: return
        destination = filedialog.asksaveasfilename(title="Save generated audio",defaultextension=".wav",filetypes=[("WAV audio","*.wav")])
        if destination: shutil.copy2(self.wav_path,destination); self.status.set(f"Saved audio to {destination}")

    def run(self): self.root.mainloop()
