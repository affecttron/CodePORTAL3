import json
import os

import settings as _s

_CONFIG_PATH = os.path.join(_s.BASE_DIR, "data", "user_config.json")

_DEFAULTS = {
    "resolution": [_s.DESIGN_WIDTH, _s.DESIGN_HEIGHT],
    "window_mode": "fullscreen",
    "sound_volume": _s.SOUND_VOLUME,
    "music_volume": _s.MUSIC_VOLUME,
    "ambience_volume": _s.AMBIENCE_VOLUME,
}

RESOLUTIONS = [
    (1280, 720),
    (1600, 900),
    (1920, 1080),
    (2560, 1440),
]

WINDOW_MODES = ["fullscreen", "windowed"]


def load() -> dict:
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        cfg = dict(_DEFAULTS)
        cfg.update({k: data[k] for k in _DEFAULTS if k in data})
        return cfg
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return dict(_DEFAULTS)


def save(cfg: dict) -> None:
    os.makedirs(os.path.dirname(_CONFIG_PATH), exist_ok=True)
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def apply(cfg: dict) -> None:
    from sound_manager import SoundManager
    sm = SoundManager()
    sm.set_volume(cfg["sound_volume"])
    sm.set_music_volume(cfg["music_volume"])
    sm.set_ambience_volume(cfg["ambience_volume"])
