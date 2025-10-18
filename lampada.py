def iniciar_lampada():
          ...
          
          return True

def atuar_sobre_lampada(acao, dispositivo):
          if acao in ["ligar", "desligar", "acender", "apagar"]:
                    sucesso = iniciar_lampada()
                    if sucesso:
                              print(f"Lâmpada {acao} com sucesso.")
                    else:
                              print(f"Falha ao {acao} a lâmpada.")