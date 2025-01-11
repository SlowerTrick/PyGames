from pydub import AudioSegment
import pygame
import io
import random

class AudioManager:
    def __init__(self):
        pygame.mixer.init()

    def play_with_pitch(self, sound, min_pitch=90, max_pitch=110, volume_change=None):
        """
        Altera o pitch e opcionalmente o volume de um som antes de reproduzi-lo.
        - sound: Objeto pygame.mixer.Sound.
        - min_pitch, max_pitch: Intervalo percentual para alterar o pitch.
        - volume_change: Valor para alterar o volume (em dB). Se None, não há alteração.
        """
        if not isinstance(sound, pygame.mixer.Sound):
            raise ValueError("O som deve ser um objeto pygame.mixer.Sound.")

        # Extrai os dados brutos do som como um AudioSegment
        raw = sound.get_raw()
        audio = AudioSegment(
            data=raw,
            sample_width=2,  # pygame usa 16 bits (2 bytes por sample)
            frame_rate=44100,
            channels=2  # Stereo
        )

        # Gera o valor de pitch aleatório entre min_pitch e max_pitch
        pitch_percent = random.uniform(min_pitch, max_pitch)
        new_rate = int(audio.frame_rate * (pitch_percent / 100))
        pitched_audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_rate})
        pitched_audio = pitched_audio.set_frame_rate(44100)

        # Se volume_change for fornecido, aplique a alteração de volume
        if volume_change is not None:
            pitched_audio = pitched_audio.apply_gain(volume_change)

        # Exporta o som modificado para BytesIO para uso com pygame
        byte_io = io.BytesIO()
        pitched_audio.export(byte_io, format='wav')
        byte_io.seek(0)

        # Carrega o som no Pygame e reproduz
        pygame_sound = pygame.mixer.Sound(byte_io)
        pygame_sound.play()