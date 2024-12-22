from pydub import AudioSegment
import pygame
import io
import random

class AudioManager:
    def __init__(self):
        pygame.mixer.init()

    def play_with_pitch(self, sound_path, min_pitch=90, max_pitch=110, volume_change=None):
        """
        Altera o pitch e opcionalmente o volume de um som antes de reproduzi-lo.
        - sound_path: Caminho do arquivo de som.
        - min_pitch, max_pitch: Intervalo percentual para alterar o pitch.
        - volume_reduction: Valor para reduzir o volume (em dB). Se None, não há redução.
        """
        # Gera o valor de pitch aleatório entre min_pitch e max_pitch
        pitch_percent = random.uniform(min_pitch, max_pitch)
        #print(f"Playing sound with pitch: {pitch_percent}%")

        # Carrega o som e altera o pitch
        sound = AudioSegment.from_file(sound_path)
        new_rate = int(sound.frame_rate * (pitch_percent / 100))
        pitched_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_rate})
        pitched_sound = pitched_sound.set_frame_rate(44100)

        # Se volume_reduction for fornecido, aplique a redução de volume
        if volume_change is not None:
            #print(f"Reducing volume by {volume_change} dB")
            pitched_sound = pitched_sound.apply_gain(volume_change)

        # Exporta o som modificado para BytesIO para uso com pygame
        byte_io = io.BytesIO()
        pitched_sound.export(byte_io, format='wav')
        byte_io.seek(0)

        # Carrega o som no Pygame e reproduz
        sound = pygame.mixer.Sound(byte_io)
        sound.play()