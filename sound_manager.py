import os
import pygame

from settings import SOUNDS_FOLDER, SOUND_VOLUME, MUSIC_VOLUME


SOUND_FILES = {
    "jump": "jump.wav",
    "correct": "correct.wav",
    "wrong": "wrong.wav",
    "portal_open": "portal_open.wav",
    "portal_complete": "portal_complete.wav",
    "death": "death.wav",
    "win": "win.wav",
    "menu_click": "menu_click.wav",
}

MUSIC_FILE = "background_music.mp3"


class SoundManager:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._sounds = {}
        self._sound_volume = SOUND_VOLUME
        self._music_volume = MUSIC_VOLUME
        self._music_path = None
        self._music_loaded = False

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error as e:
            print(f"[SoundManager] mixer init neizdevās: {e}")
            return

        self._load_sounds()
        self._prepare_music()

    def _load_sounds(self):
        for name, filename in SOUND_FILES.items():
            path = os.path.join(SOUNDS_FOLDER, filename)
            if not os.path.isfile(path):
                continue
            try:
                sound = pygame.mixer.Sound(path)
                sound.set_volume(self._sound_volume)
                self._sounds[name] = sound
            except pygame.error as e:
                print(f"[SoundManager] '{filename}' ielāde neizdevās: {e}")

    def _prepare_music(self):
        path = os.path.join(SOUNDS_FOLDER, MUSIC_FILE)
        if os.path.isfile(path):
            self._music_path = path

    def play_sound(self, sound_name):
        sound = self._sounds.get(sound_name)
        if sound is None:
            return
        try:
            sound.play()
        except pygame.error:
            pass

    def play_music(self):
        if self._music_path is None:
            return
        try:
            if not self._music_loaded:
                pygame.mixer.music.load(self._music_path)
                self._music_loaded = True
            pygame.mixer.music.set_volume(self._music_volume)
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(loops=-1)
        except pygame.error as e:
            print(f"[SoundManager] mūzikas atskaņošana neizdevās: {e}")

    def stop_music(self):
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass

    def set_volume(self, volume):
        self._sound_volume = max(0.0, min(1.0, float(volume)))
        for sound in self._sounds.values():
            sound.set_volume(self._sound_volume)

    def set_music_volume(self, volume):
        self._music_volume = max(0.0, min(1.0, float(volume)))
        try:
            pygame.mixer.music.set_volume(self._music_volume)
        except pygame.error:
            pass
