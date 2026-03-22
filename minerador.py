import socket
import json
import hashlib
import threading

# Variáveis globais para controle de interrupção
tarefa_atual = None
interromper_mineracao = False

def minerar_bloco(cliente):
    global tarefa_atual, interromper_mineracao
    
    while True:
        if tarefa_atual:
            indice = tarefa_atual['indice']
            dados = tarefa_atual['dados']
            h_anterior = tarefa_atual['hash_anterior']
            dificuldade = tarefa_atual['dificuldade']
            
            print(f"\n[TRABALHO] Iniciando mineração do Bloco {indice}...")
            nonce = 0
            interromper_mineracao = False
            
            while not interromper_mineracao:
                # Cálculo do Hash
                conteudo = f"{indice}{dados}{h_anterior}{nonce}"
                h = hashlib.sha256(conteudo.encode()).hexdigest()
                
                if h[:dificuldade] == "0" * dificuldade:
                    print(f"[SUCESSO] Bloco {indice} resolvido com Nonce {nonce}!")
                    
                    resposta = json.dumps({
                        "indice": indice,
                        "nonce": nonce,
                        "hash": h,
                        "dados": dados
                    })
                    try:
                        cliente.sendall((resposta + "\n").encode())
                    except:
                        print("[ERRO] Falha ao enviar resposta ao servidor.")
                    
                    tarefa_atual = None # Limpa a tarefa para esperar a próxima
                    break
                
                nonce += 1
                
                # Checagem rápida para ver se o servidor mandou algo novo enquanto calculávamos
                if nonce % 1000 == 0 and interromper_mineracao:
                    print(f"[CANCELADO] Alguém já resolveu o Bloco {indice}. Parando...")
                    break

def escutar_servidor(cliente):
    global tarefa_atual, interromper_mineracao
    buffer = ""
    
    while True:
        try:
            dados_recebidos = cliente.recv(4096).decode()
            if not dados_recebidos: break
            
            buffer += dados_recebidos
            while "\n" in buffer:
                msg, buffer = buffer.split("\n", 1)
                if not msg.strip(): continue
                
                nova_tarefa = json.loads(msg)
                
                # Se recebemos uma tarefa nova, avisamos o loop de mineração para parar
                print(f"\n[REDE] Recebido desafio para Bloco {nova_tarefa['indice']}")
                tarefa_atual = nova_tarefa
                interromper_mineracao = True 
        except:
            break

def iniciar_minerador():
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        cliente.connect(('localhost', 5000))
        print("="*40)
        print(" MINERADOR CONECTADO E COMPETINDO ")
        print("="*40)

        # Thread para ouvir o servidor enquanto a CPU minera
        threading.Thread(target=escutar_servidor, args=(cliente,), daemon=True).start()
        
        # Inicia a função de mineração no thread principal
        minerar_bloco(cliente)
        
    except ConnectionRefusedError:
        print("[ERRO] O servidor está offline.")

if __name__ == "__main__":
    iniciar_minerador()