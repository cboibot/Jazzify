from pathlib import Path
import winsound


def play_wav(path: Path) -> None:
    winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)


def stop() -> None:
    winsound.PlaySound(None, 0)
