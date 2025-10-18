from flask import Flask, Response, request, send_from_directory
from nltk import word_tokenize, corpus
from inicializador_modelo import *
from transcritor import *
from threading import Thread
import secrets
import pyaudio
import wave
import json
import os

from lampada import *
from som import *

LINGUAGEM = "portuguese"
FORMATO = pyaudio.paInt16
CANAIS = 1
AMOSTRAS = 1024
TEMPO_GRAVACAO = 5
CAMINHO_AUDIO_FALAS = "C:\\Users\\marco\\Desktop\\assistente_virtual\\temp"
CONFIGURACOES = "C:\\Users\\marco\\Desktop\\assistente_virtual\\config.json"

MODO_LINHA_COMANDO = 1
MODO_WEB = 2
MODO_DE_FUNCIONAMENTO = MODO_WEB

def iniciar(dispositivo):
          modelo_iniciado, processador, modelo = iniciar_modelo(MODELOS[0], dispositivo)
          
          gravador = pyaudio.PyAudio()

          palavras_de_parada = set(corpus.stopwords.words(LINGUAGEM))
          
          with open(CONFIGURACOES, 'r', encoding='utf-8') as arquivo_configuracoes:
                    configuracoes = json.load(arquivo_configuracoes)
                    acoes = configuracoes["acoes"]
                    arquivo_configuracoes.close()

          return modelo_iniciado, processador, modelo, gravador, palavras_de_parada, acoes

def iniciar_atuadores():
          atuadores = []
          
          if iniciar_lampada():
                    atuadores.append({
                              "nome": "lâmpada",
                              "atuacao": atuar_sobre_lampada
                    })
                    
          if iniciar_som():
                    atuadores.append({
                              "nome": "sistema de som",
                              "atuacao": atuar_sobre_som
                    })
                    
          return atuadores



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

def processar_transcricao(transcricao, palavras_de_parada):
          comando = []
          
          tokens = word_tokenize(transcricao)

          for token in tokens:
                    if token not in palavras_de_parada:
                              comando.append(token)

          return comando

def validar_comando(comando, acoes):
          valido, acao, dispositivo = False, None, None
          
          if len(comando) >= 2:
                    acao = comando[0]
                    dispositivo = comando[1]
                    
                    for acao_prevista in acoes:
                              if acao == acao_prevista["nome"]:
                                        if dispositivo in acao_prevista["dispositivos"]:
                                                  valido = True
                                                  break
          
          return valido, acao, dispositivo

def atuar(acao, dispositivo, atuadores):
          for atuador in atuadores: 
                    print(f"enviando comando para {atuador['nome']}")
                    atuacao = Thread(target=atuador['atuacao'], args=[acao, dispositivo])
                    atuacao.start()
                    


def ativar_linha_de_comando():
          while True:
                    fala = capturar_fala(gravador)
                    gravado, arquivo = gravar_fala(gravador, fala)
                    if gravado:
                    
                              fala = carregar_fala(arquivo)
                                        
                              transcricao = transcrever_fala(dispositivo, fala, modelo, processador)
                                        
                              if os.path.exists(arquivo):
                                        os.remove(arquivo) 
                                                  # Apaga o arquivo temporário após a transcrição
                              comando = processar_transcricao(transcricao, palavras_de_parada)
                              print(f"Comando: {comando}") 
                                        
                              valido, acao, dispositivo_alvo = validar_comando(comando, acoes)  
                              if valido:
                                        print(f"Comando válido: {acao} no {dispositivo_alvo}")
                                        atuar(acao, dispositivo_alvo, atuadores)
                              else:
                                        print("Comando inválido ou não reconhecido.")
                    else:
                              print("Ocorreu um erro ao gravar o áudio")
                              
                              
############################ SERVIÇO WEB ###########################################       
servico = Flask("assistente", static_folder="public")

@servico.get("/")
def acessar_pagina():
          return send_from_directory("public", "index.html")

@servico.get("/<path:caminho>")
def acessar_pasta_estatica(caminho):
          return send_from_directory("public", caminho)

@servico.post("/reconhecer_comando")
def reconhecer_comando():
          if "audio" not in request.files:
                    return Response(status=400)
          audio = request.files["audio"]
          
          caminho_arquivo = f"{CAMINHO_AUDIO_FALAS}\\fala_{secrets.token_hex(32).lower()}.wav"
          audio.save(caminho_arquivo)
          
          try:
                    trasncricao = transcrever_fala(servico.config['dispositivo'], carregar_fala(caminho_arquivo), servico.config['modelo'], servico.config['processador'])
                    comando = processar_transcricao(transcricao, servico.config['palavras_de_parada'])
                    valido, acao, dispositivo_alvo = validar_comando(comando, servico.config["acoes"])
                    
                    if valido:
                              print(f"Comando válido, executar atuação")
                              atuar(acao, dispositivo_alvo, servico.config['atuadores'])
                              return Response(json.dumps({"transquição": transcricao}), status=200)
                    else:
                              return Response(json.dumps({"transquição": "Comando não reconhecido"}), status=200)
                              
                   
                    
          except Exception as e:
                    print(f"erro ao processar fala: {str(e)}")
                    
                    return Response(status=500)
          finally:
                    if os.path.exists(caminho_arquivo):
                              os.remove(caminho_arquivo)    
                                
#############################################################################################     


def ativar_web(dispositivo, modelo, processador, palavras_de_parada, acoes, atuadores):
          servico.config["dispositivo"] = dispositivo
          servico.config["modelo"] = modelo
          servico.config["processador"] = processador
          servico.config["palavras_de_parada"] = palavras_de_parada
          servico.config["acoes"] = acoes
          servico.config["atuadores"] = atuadores
          
          servico.run(port=7100)
          
if __name__ == "__main__":
          dispositivo = "cuda:0" if torch.cuda.is_available() else "cpu"

          iniciado, processador, modelo, gravador, palavras_de_parada, acoes = iniciar(dispositivo)

          if iniciado:
                    
                    atuadores = iniciar_atuadores()
                    if MODO_DE_FUNCIONAMENTO == MODO_LINHA_COMANDO:
                              ativar_linha_de_comando()
                    elif MODO_DE_FUNCIONAMENTO == MODO_WEB:
                              ativar_web(dispositivo, modelo, processador, palavras_de_parada, acoes, atuadores)
                    else: 
                              print("Modo de funcionamento não implementado")
          else:
                    print("Ocorreu um erro de inicialização")