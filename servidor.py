import socket
import json
import threading
import random
import time
import os
import hashlib
from datetime import datetime
from flask import Flask, jsonify
from identidade import gerar_chaves, assinar_dados, exportar_chave_publica

servidor_app = Flask(__name__)
servidor_instancia = None


class ServidorBlockchain:
    def __init__(self):
        self.host = os.getenv("SERVER_HOST", "0.0.0.0")
        self.porta = int(os.getenv("SERVER_PORT", "5000"))
        self.porta_controle = int(os.getenv("SERVER_CONTROL_PORT", "5001"))
        self.min_mineradores_inicio = int(os.getenv("MIN_MINERADORES_INICIO", "4"))
        self.dificuldade = int(os.getenv("DIFFICULDADE", "5"))

        self.mineradores = {}
        self.historico_blocos = []
        self.cadeia_referencia = {
            "tamanho": 1,
            "ultimo_hash": "GENESIS",
            "minerador": "genesis",
        }

        self.bloco_atual_resolvido = True
        self.desafio_atual = None
        self._aguardo_mineradores_logado = False
        self.lock = threading.Lock()

        self.entidades_emissoras = self._inicializar_entidades_emissoras()

    def _inicializar_entidades_emissoras(self):
        entidades = [
            "Cartório Lucena",
            "Cartório Marques",
            "Cartório Barreto",
            "Segurança Pública do RN",
            "Governo Federal",
        ]
        emissoras = {}
        for nome in entidades:
            chave_privada, chave_publica = gerar_chaves()
            emissoras[nome] = {
                "chave_privada": chave_privada,
                "chave_publica_pem": exportar_chave_publica(chave_publica),
            }
        return emissoras

    def _liberar_punicoes_expiradas(self):
        agora = time.time()
        for dados in self.mineradores.values():
            punido_ate = dados.get("punido_ate", 0)
            if punido_ate and punido_ate <= agora:
                dados["punido_ate"] = 0
                dados["status"] = "ativo"

    def _atualizar_referencia_maior_cadeia(self):
        maior = {
            "tamanho": 1,
            "ultimo_hash": "GENESIS",
            "minerador": "genesis",
            "ultima_atualizacao": 0,
        }

        for minerador_id, dados in self.mineradores.items():
            tamanho = int(dados.get("cadeia_tamanho", 1))
            ultimo_hash = dados.get("ultimo_hash", "GENESIS")
            ultima_atualizacao = float(dados.get("ultima_atualizacao_cadeia", 0))

            if tamanho > maior["tamanho"]:
                maior = {
                    "tamanho": tamanho,
                    "ultimo_hash": ultimo_hash,
                    "minerador": minerador_id,
                    "ultima_atualizacao": ultima_atualizacao,
                }
                continue

            if tamanho == maior["tamanho"] and ultima_atualizacao > maior["ultima_atualizacao"]:
                maior = {
                    "tamanho": tamanho,
                    "ultimo_hash": ultimo_hash,
                    "minerador": minerador_id,
                    "ultima_atualizacao": ultima_atualizacao,
                }

        self.cadeia_referencia = {
            "tamanho": maior["tamanho"],
            "ultimo_hash": maior["ultimo_hash"],
            "minerador": maior["minerador"],
        }

    def _estado_minerador_publico(self, minerador_id, dados):
        punido_ate = dados.get("punido_ate", 0)
        restante = max(0, int(punido_ate - time.time())) if punido_ate else 0
        status = "punido" if restante > 0 else dados.get("status", "ativo")
        return {
            "nome": minerador_id,
            "blocos_resolvidos": dados.get("blocos_resolvidos", 0),
            "status": status,
            "consecutivos": dados.get("consecutivos", 0),
            "punido_ate": punido_ate,
            "punicao_restante_segundos": restante,
            "cadeia_tamanho": int(dados.get("cadeia_tamanho", 1)),
            "ultimo_hash": dados.get("ultimo_hash", "GENESIS"),
        }

    def estado_publico(self):
        with self.lock:
            self._liberar_punicoes_expiradas()
            self._atualizar_referencia_maior_cadeia()
            return {
                "mineradores": {
                    minerador_id: self._estado_minerador_publico(minerador_id, dados)
                    for minerador_id, dados in self.mineradores.items()
                },
                "blocos_minerados": list(self.historico_blocos),
                "cadeia_referencia": dict(self.cadeia_referencia),
                "bloco_atual_resolvido": self.bloco_atual_resolvido,
                "desafio_atual": dict(self.desafio_atual) if self.desafio_atual else None,
                "mineradores_conectados": len([d for d in self.mineradores.values() if d.get("conexao")]),
            }

    def registrar_minerador(self, conexao, endereco, minerador_id):
        with self.lock:
            dados = self.mineradores.get(minerador_id, {})
            dados.update(
                {
                    "conexao": conexao,
                    "endereco": endereco,
                    "blocos_resolvidos": dados.get("blocos_resolvidos", 0),
                    "consecutivos": dados.get("consecutivos", 0),
                    "status": dados.get("status", "ativo"),
                    "punido_ate": dados.get("punido_ate", 0),
                    "punicoes": dados.get("punicoes", 0),
                    "cadeia_tamanho": dados.get("cadeia_tamanho", 1),
                    "ultimo_hash": dados.get("ultimo_hash", "GENESIS"),
                    "ultima_atualizacao_cadeia": time.time(),
                }
            )
            self.mineradores[minerador_id] = dados
            self._atualizar_referencia_maior_cadeia()
            print(f"[CONEXÃO] Minerador registrado: {minerador_id} ({endereco})")

    def remover_minerador(self, minerador_id):
        with self.lock:
            dados = self.mineradores.pop(minerador_id, None)
            if dados:
                print(f"[CONEXÃO] Minerador removido: {minerador_id}")
                self._atualizar_referencia_maior_cadeia()

    def atualizar_status_cadeia(self, minerador_id, resposta):
        with self.lock:
            dados_minerador = self.mineradores.get(minerador_id)
            if not dados_minerador:
                return

            dados_minerador["cadeia_tamanho"] = int(resposta.get("cadeia_tamanho", 1))
            dados_minerador["ultimo_hash"] = resposta.get("ultimo_hash", "GENESIS")
            dados_minerador["ultima_atualizacao_cadeia"] = time.time()
            self._atualizar_referencia_maior_cadeia()

    def gerenciar_minerador(self, conexao, endereco):
        minerador_id = None
        print(f"[CONEXÃO] Novo minerador: {endereco}")

        buffer = ""
        try:
            while True:
                dados = conexao.recv(4096).decode()
                if not dados:
                    break

                buffer += dados
                while "\n" in buffer:
                    msg, buffer = buffer.split("\n", 1)
                    if not msg.strip():
                        continue

                    resposta = json.loads(msg)
                    if resposta.get("tipo") == "hello" or not minerador_id:
                        minerador_id = resposta.get("minerador", minerador_id or f"{endereco[0]}:{endereco[1]}")
                        self.registrar_minerador(conexao, endereco, minerador_id)
                        continue

                    if resposta.get("tipo") == "status_cadeia":
                        if minerador_id:
                            self.atualizar_status_cadeia(minerador_id, resposta)
                        continue

                    minerador_msg = resposta.get("minerador", minerador_id)
                    if minerador_msg and minerador_msg != minerador_id:
                        minerador_id = minerador_msg
                        self.registrar_minerador(conexao, endereco, minerador_id)

                    if minerador_id:
                        self.processar_vitoria(resposta, endereco, minerador_id)
        except Exception:
            pass
        finally:
            if minerador_id:
                self.remover_minerador(minerador_id)
            conexao.close()

    def processar_vitoria(self, resposta, endereco, minerador_id):
        with self.lock:
            self._liberar_punicoes_expiradas()
            dados_minerador = self.mineradores.get(minerador_id)
            if not dados_minerador:
                return

            if dados_minerador.get("punido_ate", 0) > time.time():
                print(f"[PUNIÇÃO] {minerador_id} tentou validar bloco durante o bloqueio.")
                return

            indice_recebido = int(resposta.get("indice"))
            if self.bloco_atual_resolvido or not self.desafio_atual:
                return

            indice_esperado = int(self.desafio_atual.get("indice", -1))
            hash_anterior_esperado = self.desafio_atual.get("hash_anterior", "GENESIS")
            dificuldade_esperada = int(self.desafio_atual.get("dificuldade", self.dificuldade))

            if indice_recebido != indice_esperado:
                return

            nonce = resposta.get("nonce")
            hash_recebido = resposta.get("hash")
            dados_bloco = resposta.get("dados")
            conteudo = f"{indice_recebido}{dados_bloco}{hash_anterior_esperado}{nonce}"
            hash_calculado = hashlib.sha256(conteudo.encode()).hexdigest()

            if hash_calculado != hash_recebido or not hash_recebido.startswith("0" * dificuldade_esperada):
                print(f"[CONSENSO] Bloco {indice_recebido} de {minerador_id} inválido para a cadeia de referência.")
                return

            cadeia_tamanho_reportada = int(resposta.get("cadeia_tamanho", indice_recebido + 1))
            ultimo_hash_reportado = resposta.get("ultimo_hash", hash_recebido)
            if cadeia_tamanho_reportada < indice_recebido + 1:
                cadeia_tamanho_reportada = indice_recebido + 1

            self.bloco_atual_resolvido = True
            self.desafio_atual = None
            self.historico_blocos.append(
                {
                    "indice": indice_recebido,
                    "minerador": minerador_id,
                    "nonce": nonce,
                    "hash": hash_recebido[:16],
                    "timestamp": datetime.now().isoformat(),
                }
            )

            dados_minerador["cadeia_tamanho"] = max(dados_minerador.get("cadeia_tamanho", 1), cadeia_tamanho_reportada)
            dados_minerador["ultimo_hash"] = ultimo_hash_reportado
            dados_minerador["ultima_atualizacao_cadeia"] = time.time()

            dados_minerador["blocos_resolvidos"] = dados_minerador.get("blocos_resolvidos", 0) + 1
            dados_minerador["consecutivos"] = dados_minerador.get("consecutivos", 0) + 1
            dados_minerador["status"] = "ativo"

            for outro_id, outro_dados in self.mineradores.items():
                if outro_id != minerador_id:
                    outro_dados["consecutivos"] = 0

            if dados_minerador["consecutivos"] >= 5:
                dados_minerador["punido_ate"] = time.time() + 180
                dados_minerador["status"] = "punido"
                dados_minerador["consecutivos"] = 0
                dados_minerador["punicoes"] = dados_minerador.get("punicoes", 0) + 1
                print(f"[PUNIÇÃO] {minerador_id} bloqueado por 3 minutos após 5 vitórias consecutivas.")

            self._atualizar_referencia_maior_cadeia()

            print("\n" + "!" * 50)
            print(f"VENCEDOR: {minerador_id} | {endereco}")
            print(
                f"Bloco #{indice_recebido} aceito. Cadeia válida atual: "
                f"{self.cadeia_referencia['tamanho']} blocos ({self.cadeia_referencia['minerador']})."
            )
            print("!" * 50)

    def gerador_de_desafios(self):
        emissores = list(self.entidades_emissoras.keys())
        autores_documentos = [
            "Lucas Marques",
            "Naruto Uzumaki",
            "Ana Clara Souza",
            "Maria Eduarda Lima",
            "Joao Pedro Santos",
            "Carla Beatriz Oliveira",
            "Bruno Henrique Costa",
            "Fernanda Alves Pereira",
        ]
        docs = [
            "Contrato_Social",
            "Escritura_Terreno",
            "Diploma_Digital",
            "Nota_Fiscal",
            "CPF",
            "Certidao_de_Nascimento",
            "Certidao_de_Divorcio",
            "Certidao_de_Casamento",
        ]

        while True:
            time.sleep(5)

            with self.lock:
                self._liberar_punicoes_expiradas()
                self._atualizar_referencia_maior_cadeia()
                mineradores_ativos = {
                    minerador_id: dados
                    for minerador_id, dados in self.mineradores.items()
                    if dados.get("conexao") and dados.get("punido_ate", 0) <= time.time()
                }
                conectados = len([dados for dados in self.mineradores.values() if dados.get("conexao")])

            if conectados < self.min_mineradores_inicio:
                if not self._aguardo_mineradores_logado:
                    print(
                        f"[SISTEMA] Aguardando mineradores ({conectados}/{self.min_mineradores_inicio}) para iniciar desafios..."
                    )
                    self._aguardo_mineradores_logado = True
                continue

            if self._aguardo_mineradores_logado:
                print(f"[SISTEMA] Pool mínimo atingido ({conectados}/{self.min_mineradores_inicio}). Iniciando mineração.")
                self._aguardo_mineradores_logado = False

            if len(mineradores_ativos) > 0 and self.bloco_atual_resolvido:
                proximo_indice = int(self.cadeia_referencia.get("tamanho", 1))
                hash_anterior = self.cadeia_referencia.get("ultimo_hash", "GENESIS")

                autor = random.choice(autores_documentos)
                emissor = random.choice(emissores)
                tipo = random.choice(docs)
                hash_fake = f"sha256_{random.getrandbits(64):016x}"
                dados_emissor = self.entidades_emissoras[emissor]
                assinatura_digital = assinar_dados(dados_emissor["chave_privada"], hash_fake)

                dados_payload = {
                    "documento": tipo,
                    "entidade_emissora": emissor,
                    "autor_nome": autor,
                    "hash_arquivo": hash_fake,
                    "assinatura_emissor": assinatura_digital,
                    "chave_publica_emissor": dados_emissor["chave_publica_pem"],
                }

                tarefa = {
                    "indice": proximo_indice,
                    "dados": json.dumps(dados_payload),
                    "hash_anterior": hash_anterior,
                    "dificuldade": self.dificuldade,
                }

                self.bloco_atual_resolvido = False
                self.desafio_atual = dict(tarefa)
                mensagem = (json.dumps(tarefa) + "\n").encode()
                destinatarios = list(mineradores_ativos.keys())

                print(
                    f"\n[SISTEMA] Documento Assinado! Disparando Bloco #{proximo_indice} "
                    f"com referência em {self.cadeia_referencia['minerador']}..."
                )

                for minerador_id in destinatarios:
                    dados_minerador = mineradores_ativos.get(minerador_id)
                    if not dados_minerador:
                        continue
                    try:
                        dados_minerador["conexao"].sendall(mensagem)
                    except Exception:
                        self.remover_minerador(minerador_id)

    def iniciar_api_controle(self):
        servidor_app.run(
            host=self.host,
            port=self.porta_controle,
            debug=False,
            use_reloader=False,
        )

    def iniciar(self):
        global servidor_instancia
        servidor_instancia = self

        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((self.host, self.porta))
        servidor.listen(10)

        threading.Thread(target=self.gerador_de_desafios, daemon=True).start()
        threading.Thread(target=self.iniciar_api_controle, daemon=True).start()

        print("\n" + "=" * 50)
        print(" SERVIDOR BLOCKCHAIN COM REGRA DA MAIOR CADEIA ")
        print(" Emissores autorizados:")
        for nome in self.entidades_emissoras.keys():
            print(f"  - {nome}")
        print(f" Host: {self.host} | Porta: {self.porta} | Controle HTTP: {self.porta_controle}")
        print("=" * 50)

        while True:
            conn, addr = servidor.accept()
            t = threading.Thread(target=self.gerenciar_minerador, args=(conn, addr), daemon=True)
            t.start()


@servidor_app.route("/api/estado")
def api_estado_controle():
    if servidor_instancia is None:
        return jsonify({"erro": "Servidor ainda inicializando."}), 503
    return jsonify(servidor_instancia.estado_publico())


if __name__ == "__main__":
    s = ServidorBlockchain()
    s.iniciar()
