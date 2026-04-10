import argparse
import hashlib
import json
import os
import socket
import threading
import time

try:
    from kafka import KafkaConsumer, KafkaProducer
    from kafka.errors import NoBrokersAvailable
except ImportError:
    KafkaConsumer = None
    KafkaProducer = None
    NoBrokersAvailable = Exception

tarefa_atual = None
interromper_mineracao = False

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
KAFKA_SERVERS = [s.strip() for s in KAFKA_BOOTSTRAP.split(",") if s.strip()]
SERVER_HOST = os.getenv("SERVER_HOST", "blockchain-servidor")
SERVER_PORT = int(os.getenv("SERVER_PORT", "5000"))
TOPICO_BLOCO = "blocos_minerados"


def hash_valido_do_bloco(bloco):
    conteudo = f"{bloco['indice']}{bloco['dados']}{bloco['hash_anterior']}{bloco['nonce']}"
    calculado = hashlib.sha256(conteudo.encode()).hexdigest()
    return calculado == bloco["hash"] and calculado[:bloco["dificuldade"]] == "0" * bloco["dificuldade"]


def criar_produtor_kafka():
    if KafkaProducer is None:
        raise RuntimeError("Instale kafka-python para usar o Kafka.")

    return KafkaProducer(
        bootstrap_servers=KAFKA_SERVERS,
        value_serializer=lambda valor: json.dumps(valor).encode("utf-8"),
    )


def criar_consumidor_kafka(minerador_id):
    if KafkaConsumer is None:
        raise RuntimeError("Instale kafka-python para usar o Kafka.")

    return KafkaConsumer(
        TOPICO_BLOCO,
        bootstrap_servers=KAFKA_SERVERS,
        group_id=f"{TOPICO_BLOCO}-{minerador_id}",
        auto_offset_reset="latest",
        enable_auto_commit=True,
        value_deserializer=lambda valor: json.loads(valor.decode("utf-8")),
    )


def aguardar_servidor(cliente):
    while True:
        try:
            cliente.connect((SERVER_HOST, SERVER_PORT))
            break
        except OSError:
            print(f"[BOOT] Aguardando servidor em {SERVER_HOST}:{SERVER_PORT}...")
            time.sleep(2)


def aguardar_produtor_kafka():
    while True:
        try:
            return criar_produtor_kafka()
        except Exception as erro:
            print(f"[BOOT] Aguardando Kafka em {KAFKA_BOOTSTRAP}... ({erro})")
            time.sleep(2)


def minerar_bloco(cliente, minerador_id, produtor_kafka):
    global tarefa_atual, interromper_mineracao
    
    while True:
        if tarefa_atual:
            indice = tarefa_atual['indice']
            dados = tarefa_atual['dados']
            h_anterior = tarefa_atual['hash_anterior']
            dificuldade = tarefa_atual['dificuldade']
            
            print(f"\n[{minerador_id}] [TRABALHO] Iniciando mineração do Bloco {indice}...")
            nonce = 0
            interromper_mineracao = False
            
            while not interromper_mineracao:
                # Cálculo do Hash
                conteudo = f"{indice}{dados}{h_anterior}{nonce}"
                h = hashlib.sha256(conteudo.encode()).hexdigest()
                
                if h[:dificuldade] == "0" * dificuldade:
                    print(f"[{minerador_id}] [SUCESSO] Bloco {indice} resolvido com Nonce {nonce}!")

                    bloco_minerado = {
                        "indice": indice,
                        "dados": dados,
                        "hash_anterior": h_anterior,
                        "dificuldade": dificuldade,
                        "nonce": nonce,
                        "hash": h,
                        "minerador": minerador_id,
                    }

                    try:
                        produtor_kafka.send(TOPICO_BLOCO, bloco_minerado)
                        produtor_kafka.flush()
                        print(f"[{minerador_id}] [KAFKA] Bloco disseminado para os demais mineradores.")
                    except Exception:
                        print(f"[{minerador_id}] [ERRO] Falha ao publicar o bloco no Kafka.")
                    
                    resposta = json.dumps({
                        "indice": indice,
                        "nonce": nonce,
                        "hash": h,
                        "dados": dados,
                        "minerador": minerador_id
                    })
                    try:
                        cliente.sendall((resposta + "\n").encode())
                    except:
                        print(f"[{minerador_id}] [ERRO] Falha ao enviar resposta ao servidor.")
                    
                    tarefa_atual = None # Limpa a tarefa para esperar a próxima
                    break
                
                nonce += 1
                
                # Checagem rápida para ver se o servidor mandou algo novo enquanto calculávamos
                if nonce % 1000 == 0 and interromper_mineracao:
                    print(f"[{minerador_id}] [CANCELADO] Alguém já resolveu o Bloco {indice}. Parando...")
                    break

def escutar_servidor(cliente, minerador_id):
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
                print(f"\n[{minerador_id}] [REDE] Recebido desafio para Bloco {nova_tarefa['indice']}")
                tarefa_atual = nova_tarefa
                interromper_mineracao = True 
        except:
            break


def escutar_kafka(minerador_id):
    global tarefa_atual, interromper_mineracao

    try:
        consumidor = criar_consumidor_kafka(minerador_id)
    except Exception as erro:
        print(f"[{minerador_id}] [ERRO] Kafka indisponível: {erro}")
        return

    for mensagem in consumidor:
        try:
            bloco_minerado = mensagem.value
            if not isinstance(bloco_minerado, dict):
                continue

            origem = bloco_minerado.get("minerador", "desconhecido")
            indice = bloco_minerado.get("indice")

            print(f"\n[{minerador_id}] [KAFKA] Bloco {indice} disseminado por {origem}.")

            if tarefa_atual and indice == tarefa_atual.get("indice") and hash_valido_do_bloco(bloco_minerado):
                tarefa_atual = None
                interromper_mineracao = True
                print(f"[{minerador_id}] [KAFKA] Mineração do Bloco {indice} interrompida.")
        except Exception:
            continue

def iniciar_minerador(minerador_id="Minerador"):
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        aguardar_servidor(cliente)
        produtor_kafka = aguardar_produtor_kafka()
        # As threads de recepção precisam estar prontas antes do primeiro desafio
        # para não perder a mensagem inicial enviada pelo servidor.
        threading.Thread(target=escutar_servidor, args=(cliente, minerador_id), daemon=True).start()
        threading.Thread(target=escutar_kafka, args=(minerador_id,), daemon=True).start()
        try:
            hello = json.dumps({"tipo": "hello", "minerador": minerador_id}) + "\n"
            cliente.sendall(hello.encode())
        except Exception:
            print(f"[{minerador_id}] [ERRO] Falha ao registrar identificacao no servidor.")
        print("="*40)
        print(f" {minerador_id.upper()} CONECTADO E COMPETINDO ")
        print("="*40)

        # Inicia a função de mineração no thread principal
        minerar_bloco(cliente, minerador_id, produtor_kafka)
        
    except ConnectionRefusedError:
        print(f"[{minerador_id}] [ERRO] O servidor está offline.")
    except (RuntimeError, NoBrokersAvailable) as erro:
        print(f"[{minerador_id}] [ERRO] Kafka indisponível: {erro}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inicia um minerador da blockchain.")
    parser.add_argument("--id", default="Minerador", help="Identificador exibido nos logs.")
    args = parser.parse_args()

    iniciar_minerador(args.id)
