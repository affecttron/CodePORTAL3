import os
import random
import pygame

from settings import (
    SOUNDS_FOLDER, SOUND_VOLUME, MUSIC_VOLUME,
    AMBIENCE_VOLUME, AMBIENCE_MIN_GAP_MS, AMBIENCE_MAX_GAP_MS,
    AMBIENCE_INITIAL_DELAY_MS,
)


SOUND_FILES = {
    "jump": "jump.wav",
    "correct": "correct.wav",
    "wrong": "wrong.wav",
    "portal_open": "portal_open.wav",
    "portal_complete": "portal_complete.wav",
    "death": "death.wav",
    "win": "win.wav",
    "menu_click": "menu_click.wav",
    "keystroke": "keystroke.wav",
}


SOUND_VOLUME_OVERRIDES = {
    "keystroke": 0.25,
}

MUSIC_FILE = "background_music.mp3"

AMBIENCE_FOLDER = "ambience"
AMBIENCE_EXTS = (".wav", ".ogg", ".mp3")
AMBIENCE_CHANNEL_ID = 7


class SoundManager:

    _instance = None

    # Atgriež vienīgo SoundManager instanci
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    # Inicializē audio sistēmu vienreiz
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._sounds = {}
        self._sound_volume = SOUND_VOLUME
        self._music_volume = MUSIC_VOLUME
        self._music_path = None
        self._music_loaded = False

        self._ambience_sounds = []
        self._ambience_volume = AMBIENCE_VOLUME
        self._ambience_channel = None
        self._ambience_enabled = False
        self._next_ambience_ms = 0

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error as e:
            print(f"[SoundManager] mixer init neizdevās: {e}")
            return

        self._load_sounds()
        self._prepare_music()
        self._load_ambience()

    # Ielādē visas spēles skaņas no failiem
    def _load_sounds(self):
        for name, filename in SOUND_FILES.items():
            path = os.path.join(SOUNDS_FOLDER, filename)
            if not os.path.isfile(path):
                continue
            try:
                sound = pygame.mixer.Sound(path)
                multiplier = SOUND_VOLUME_OVERRIDES.get(name, 1.0)
                sound.set_volume(self._sound_volume * multiplier)
                self._sounds[name] = sound
            except pygame.error as e:
                print(f"[SoundManager] '{filename}' ielāde neizdevās: {e}")

    # Sagatavo mūzikas faila ceļu
    def _prepare_music(self):
        path = os.path.join(SOUNDS_FOLDER, MUSIC_FILE)
        if os.path.isfile(path):
            self._music_path = path

    # Ielādē fona ambient skaņas
    def _load_ambience(self):
        folder = os.path.join(SOUNDS_FOLDER, AMBIENCE_FOLDER)
        if not os.path.isdir(folder):
            return
        try:
            self._ambience_channel = pygame.mixer.Channel(AMBIENCE_CHANNEL_ID)
        except pygame.error:
            self._ambience_channel = None
            return
        for filename in sorted(os.listdir(folder)):
            if not filename.lower().endswith(AMBIENCE_EXTS):
                continue
            path = os.path.join(folder, filename)
            try:
                sound = pygame.mixer.Sound(path)
                sound.set_volume(self._ambience_volume)
                self._ambience_sounds.append(sound)
            except pygame.error as e:
                print(f"[SoundManager] ambient '{filename}' neielādēts: {e}")

    # Sāk ambient skaņu atskaņošanu
    def start_ambience(self):
        if not self._ambience_sounds or self._ambience_channel is None:
            return
        self._ambience_enabled = True
        self._schedule_next_ambience(initial=True)

    # Apstādina ambient skaņas
    def stop_ambience(self):
        self._ambience_enabled = False
        if self._ambience_channel is not None:
            try:
                self._ambience_channel.stop()
            except pygame.error:
                pass

    # Atjaunina ambient stāvokli kadrā
    def update_ambience(self):
        if not self._ambience_enabled or self._ambience_channel is None:
            return
        if self._ambience_channel.get_busy():
            return
        if pygame.time.get_ticks() < self._next_ambience_ms:
            return
        sound = random.choice(self._ambience_sounds)
        sound.set_volume(self._ambience_volume)
        try:
            self._ambience_channel.play(sound)
        except pygame.error:
            pass
        self._schedule_next_ambience(initial=False)

    # Plāno nākamās ambient skaņas laiku
    def _schedule_next_ambience(self, initial):
        if initial:
            gap = AMBIENCE_INITIAL_DELAY_MS
        else:
            gap = random.randint(AMBIENCE_MIN_GAP_MS, AMBIENCE_MAX_GAP_MS)
        self._next_ambience_ms = pygame.time.get_ticks() + gap

    # Iestata ambient skaļumu
    def set_ambience_volume(self, volume):
        self._ambience_volume = max(0.0, min(1.0, float(volume)))
        for sound in self._ambience_sounds:
            sound.set_volume(self._ambience_volume)

    # Atskaņo skaņu pēc nosaukuma
    def play_sound(self, sound_name):
        sound = self._sounds.get(sound_name)
        if sound is None:
            return
        try:
            sound.play()
        except pygame.error:
            pass

    # Sāk mūzikas atskaņošanu bezgalīgā ciklā
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
            print(f"[SoundManager] failed: {e}")

    # Apstādina mūziku
    def stop_music(self):
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass

    # Iestata efektu skaļumu
    def set_volume(self, volume):
        self._sound_volume = max(0.0, min(1.0, float(volume)))
        for name, sound in self._sounds.items():
            multiplier = SOUND_VOLUME_OVERRIDES.get(name, 1.0)
            sound.set_volume(self._sound_volume * multiplier)

    # Iestata mūzikas skaļumu
    def set_music_volume(self, volume):
        self._music_volume = max(0.0, min(1.0, float(volume)))
        try:
            pygame.mixer.music.set_volume(self._music_volume)
        except pygame.error:
            pass
