def iniciar_som():
          ...
          
          return True

def atuar_sobre_som(acao, dispositivo):
          if acao in ["tocar", "parar"] and dispositivo in ["som", "música"]:
                    sucesso = iniciar_som()
                    if sucesso:
                              print(f"Som {acao} com sucesso.")
                    else:
                              print(f"Falha ao {acao} o som.")
