import json
import os
import socket
import threading
import time
from datetime import datetime
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

try:
    from kafka import KafkaConsumer
    from kafka.errors import NoBrokersAvailable
except ImportError:
    KafkaConsumer = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'blockchain-monitor-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
KAFKA_SERVERS = [s.strip() for s in KAFKA_BOOTSTRAP.split(",") if s.strip()]
SERVER_HOST = os.getenv("SERVER_HOST", "blockchain-servidor")
SERVER_PORT = int(os.getenv("SERVER_PORT", "5000"))
TOPICO_BLOCO = "blocos_minerados"

# Estado global do monitor
estado = {
    "blockchain": [],
    "mineradores": {},
    "blocos_minerados": [],
    "ultima_atualizacao": datetime.now().isoformat(),
}


def conectar_servidor():
    """Conecta ao servidor blockchain e obtém o estado da cadeia."""
    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.settimeout(5)
        cliente.connect((SERVER_HOST, SERVER_PORT))
        cliente.close()
        return True
    except Exception as e:
        print(f"[MONITOR] Erro ao conectar ao servidor: {e}")
        return False


def escutar_blocos_kafka():
    """Escuta tópico Kafka para blocos minerados."""
    if KafkaConsumer is None:
        print("[MONITOR] Kafka-python não instalado, pulando listener.")
        return

    while True:
        try:
            consumidor = KafkaConsumer(
                TOPICO_BLOCO,
                bootstrap_servers=KAFKA_SERVERS,
                auto_offset_reset="latest",
                enable_auto_commit=True,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")) if v else None,
                group_id="monitor-blocos",
            )
            print(f"[MONITOR] Conectado ao Kafka em {KAFKA_BOOTSTRAP}")

            for mensagem in consumidor:
                if mensagem.value:
                    bloco = mensagem.value
                    minerador_id = bloco.get("minerador", "desconhecido")
                    indice = bloco.get("indice")

                    # Mantemos apenas o primeiro vencedor por índice de bloco.
                    if any(item.get("indice") == indice for item in estado["blocos_minerados"]):
                        print(f"[MONITOR] Bloco {indice} duplicado ignorado (vencedor tardio: {minerador_id}).")
                        continue

                    timestamp = datetime.now().isoformat()
                    bloco_info = {
                        "indice": indice,
                        "minerador": minerador_id,
                        "nonce": bloco.get("nonce"),
                        "hash": bloco.get("hash", "")[:16],
                        "timestamp": timestamp,
                    }

                    estado["blocos_minerados"].append(bloco_info)
                    if minerador_id not in estado["mineradores"]:
                        estado["mineradores"][minerador_id] = {
                            "nome": minerador_id,
                            "blocos_resolvidos": 0,
                            "status": "ativo",
                        }
                    estado["mineradores"][minerador_id]["blocos_resolvidos"] += 1
                    estado["ultima_atualizacao"] = timestamp

                    # Emitir evento para todos os clientes conectados
                    socketio.emit(
                        "bloco_minerado",
                        {
                            "minerador": minerador_id,
                            "indice": indice,
                            "nonce": bloco.get("nonce"),
                            "hash": bloco.get("hash", "")[:16],
                            "timestamp": timestamp,
                        },
                    )
                    print(
                        f"[MONITOR] Bloco {indice} minerado por {minerador_id} publicado via WebSocket"
                    )
        except NoBrokersAvailable:
            print("[MONITOR] Kafka indisponível, tentando reconectar...")
            time.sleep(5)
        except Exception as e:
            print(f"[MONITOR] Erro ao escutar Kafka: {e}")
            time.sleep(5)


@app.route("/")
def index():
    """Serve a página principal."""
    return render_template("index.html")


@app.route("/api/estado")
def api_estado():
    """Retorna o estado atual da blockchain."""
    return {
        "blockchain": estado["blockchain"],
        "mineradores": estado["mineradores"],
        "blocos_minerados": estado["blocos_minerados"],
        "ultima_atualizacao": estado["ultima_atualizacao"],
    }


@socketio.on("connect")
def handle_connect():
    """Evento quando cliente se conecta."""
    print(f"[MONITOR] Cliente conectado")
    emit(
        "estado_inicial",
        {
            "mineradores": estado["mineradores"],
            "blocos_minerados": estado["blocos_minerados"],
            "servidor_conectado": conectar_servidor(),
        },
    )


@socketio.on("disconnect")
def handle_disconnect():
    """Evento quando cliente se desconecta."""
    print(f"[MONITOR] Cliente desconectado")


@socketio.on("ping")
def handle_ping():
    """Responde a ping do cliente."""
    emit("pong", {"timestamp": datetime.now().isoformat()})


def iniciar_monitor():
    """Inicializa o monitor."""
    print("\n" + "=" * 50)
    print(" MONITOR BLOCKCHAIN COM WEBSOCKET ")
    print(f" Kafka: {KAFKA_BOOTSTRAP}")
    print(f" Servidor: {SERVER_HOST}:{SERVER_PORT}")
    print("=" * 50)

    # Inicia listener de Kafka em thread daemon
    thread_kafka = threading.Thread(
        target=escutar_blocos_kafka, daemon=True, name="KafkaListener"
    )
    thread_kafka.start()

    # Inicia Flask + SocketIO
    flask_host = os.getenv("FLASK_HOST", "0.0.0.0")
    flask_port = int(os.getenv("FLASK_PORT", "8080"))

    socketio.run(app, host=flask_host, port=flask_port, debug=False, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    iniciar_monitor()

