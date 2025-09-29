from inicializador_modelo import *
from transcritor import *
import secrets
import pyaudio
import wave
import os


def iniciar(dispositivo):
          modelo_iniciado, processador, modelo = iniciar_modelo(MODELOS[0], dispositivo)
          
          gravador = pyaudio.PyAudio()
          
          return modelo_iniciado, processador, modelo, gravador

FORMATO = pyaudio.paInt16
CANAIS = 1
AMOSTRAS = 1024
TEMPO_GRAVACAO = 5


def capturar_fala(gravador):
          gravacao = gravador.open(format=FORMATO, channels=CANAIS, rate=TAXA_AMOSTRAGEM, input=True, frames_per_buffer=AMOSTRAS)
          print("Fale alguma coisa...")
          
          fala = []
          for _ in range(0, int(TAXA_AMOSTRAGEM / AMOSTRAS * TEMPO_GRAVACAO)):
                    dados = gravacao.read(AMOSTRAS)
                    fala.append(dados)
          gravacao.stop_stream()
          gravacao.close()
          
          print("Gravação encerrada.")
          return fala

CAMINHO_AUDIO_FALAS = "C:\\Users\\marco\\Desktop\\assistente_virtual\\temp"

def gravar_fala(gravador, fala):
          gravado, arquivo = False, f"{CAMINHO_AUDIO_FALAS}\\fala_{secrets.token_hex(32).lower()}.wav"

          try:
                    wav = wave.open(arquivo, 'wb')
                    wav.setnchannels(CANAIS)
                    wav.setsampwidth(gravador.get_sample_size(FORMATO))
                    wav.setframerate(TAXA_AMOSTRAGEM)
                    wav.writeframes(b''.join(fala))
                    wav.close()
                    gravado = True
          except Exception as e:
                    print(f"erro ao gravar o áudio: {str(e)}")
          return gravado, arquivo


if __name__ == "__main__":
          dispositivo = "cuda:0" if torch.cuda.is_available() else "cpu"
          
          iniciado, processador, modelo, gravador = iniciar(dispositivo)
          
          if iniciado:
                    while True:
                              fala = capturar_fala(gravador)
                              gravado, arquivo = gravar_fala(gravador, fala)
                              if gravado:
                                        fala = carregar_fala(arquivo)
                                        transcricao = transcrever_fala(dispositivo, fala, modelo, processador)

                                        print(f"Transcrição: {transcricao}")
                              else:
                                        print("Ocorreu um erro ao gravar o áudio")
          else:
                    print("Ocorreu um erro de inicialização")