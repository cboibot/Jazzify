"""Central style defaults and arrangement profiles used across Jazzify."""
from dataclasses import dataclass


@dataclass(frozen=True)
class StyleDefaults:
    key: str
    bpm: int
    density_label: str
    velocity_label: str
    swing_label: str


@dataclass(frozen=True)
class GenerationProfile:
    swing: float; density: float; syncopation: float; chromaticism: float; complexity: float
    walking_bass: float; repeat: float; rest_chance: float; piano_activity: float; bass_activity: float
    drum_activity: float; solo_activity: float; low_register_bias: float; descending_bias: float
    phrase_bars: int; note_length: float; velocity_low: int; velocity_high: int; humanize: float
    piano_range: tuple[int, int]; sax_range: tuple[int, int]; trumpet_range: tuple[int, int]
    guitar_range: tuple[int, int]; bass_range: tuple[int, int]; dark_harmony: bool = False


STYLE_DEFAULTS = {
    "Jazz": StyleDefaults("C Major", 108, "Medium", "Medium", "55%"),
    "Blues": StyleDefaults("Bb Major", 96, "Medium", "Medium", "62%"),
    "Dark Jazz": StyleDefaults("D Minor", 72, "Low–Medium", "Soft", "65%"),
    "Lo-fi Jazz": StyleDefaults("A Minor", 78, "Low–Medium", "Soft", "45%"),
    "Bebop": StyleDefaults("C Major", 168, "High", "Strong", "68%"),
    "Jazz Ballad": StyleDefaults("D Minor", 64, "Low", "Soft", "20%"),
}


STYLES = {
    "Jazz": GenerationProfile(.18,.62,.45,.22,.68,.62,.36,.14,.76,.78,.68,.72,.42,.35,4,.70,52,84,.035,(48,77),(58,79),(57,82),(52,75),(28,48)),
    "Blues": GenerationProfile(.23,.56,.42,.28,.38,.76,.50,.18,.70,.80,.65,.66,.45,.30,4,.78,55,88,.045,(46,76),(56,78),(55,80),(50,74),(28,48)),
    "Dark Jazz": GenerationProfile(.13,.43,.34,.48,.84,.55,.36,.34,.62,.90,.34,.48,.82,.72,4,1.35,38,76,.025,(39,69),(53,70),(55,74),(48,68),(26,45),True),
    "Lo-fi Jazz": GenerationProfile(.09,.38,.22,.12,.34,.24,.76,.30,.50,.58,.38,.44,.66,.25,4,1.05,42,72,.055,(44,70),(55,72),(56,76),(50,70),(28,46)),
    "Bebop": GenerationProfile(.25,.88,.68,.62,.86,.94,.20,.05,.78,.92,.88,.92,.15,.18,2,.40,62,102,.030,(50,82),(64,86),(62,88),(54,78),(29,50)),
    "Jazz Ballad": GenerationProfile(.04,.31,.18,.20,.78,.28,.44,.42,.48,.60,.28,.54,.65,.50,4,1.65,36,72,.020,(42,73),(55,74),(55,77),(50,72),(27,45)),
}


MOODS = {
    "Dark": dict(density=-.10, rest_chance=.15, chromaticism=.16, low_register_bias=.20, descending_bias=.28, drum_activity=-.16, solo_activity=-.15, note_length=.12, dark_harmony=True),
    "Melancholic": dict(density=-.13, rest_chance=.16, low_register_bias=.12, descending_bias=.22, solo_activity=-.10, note_length=.25),
    "Relaxed": dict(density=-.12, rest_chance=.10, syncopation=-.10, drum_activity=-.12, walking_bass=-.16, note_length=.15),
    "Mysterious": dict(density=-.06, rest_chance=.10, chromaticism=.16, low_register_bias=.10, descending_bias=.10, dark_harmony=True),
    "Energetic": dict(density=.10, rest_chance=-.08, syncopation=.15, chromaticism=.12, drum_activity=.15, solo_activity=.14, walking_bass=.10, note_length=-.15),
    "Dreamy": dict(density=-.08, rest_chance=.12, repeat=.15, low_register_bias=.08, note_length=.20, piano_activity=-.10),
}


def style_defaults(style: str) -> StyleDefaults:
    return STYLE_DEFAULTS[style]


def profile_for(style: str, mood: str) -> GenerationProfile:
    profile, changes = STYLES[style], MOODS[mood]
    values = {name: getattr(profile, name) for name in profile.__dataclass_fields__}
    for name, change in changes.items():
        values[name] = values[name] or change if name == "dark_harmony" else values[name] + change
    for name in ("swing","density","syncopation","chromaticism","complexity","walking_bass","repeat","rest_chance","piano_activity","bass_activity","drum_activity","solo_activity","low_register_bias","descending_bias"):
        values[name] = max(0.0, min(1.0, values[name]))
    return GenerationProfile(**values)
