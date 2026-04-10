import socket
import json
import threading
import random
import time
import os
from datetime import datetime
from flask import Flask, jsonify, request
from blockchain import Blockchain
from bloco import Bloco
from identidade import gerar_chaves, assinar_dados, exportar_chave_publica

servidor_app = Flask(__name__)
servidor_instancia = None

class ServidorBlockchain:
    def __init__(self):
        self.host = os.getenv("SERVER_HOST", "0.0.0.0")
        self.porta = int(os.getenv("SERVER_PORT", "5000"))
        self.porta_controle = int(os.getenv("SERVER_CONTROL_PORT", "5001"))
        self.min_mineradores_inicio = int(os.getenv("MIN_MINERADORES_INICIO", "4"))
        self.blockchain = Blockchain()
        self.mineradores = {}
        self.historico_blocos = []
        self.bloco_atual_resolvido = True # Começa como True para o gerador iniciar
        self.ataque_ativo = False
        self.minerador_ataque = None
        self._aguardo_mineradores_logado = False
        self.lock = threading.Lock()

        # --- IDENTIDADE DO SERVIDOR ---
        # O servidor gera seu par de chaves ao iniciar
        self.chave_privada, self.chave_publica = gerar_chaves()
        # Exportamos a pública para formato PEM (string) para enviar via JSON
        self.chave_publica_pem = exportar_chave_publica(self.chave_publica)
        # ------------------------------------------

    def _liberar_punicoes_expiradas(self):
        agora = time.time()
        for minerador_id, dados in self.mineradores.items():
            punido_ate = dados.get("punido_ate", 0)
            if punido_ate and punido_ate <= agora:
                dados["punido_ate"] = 0
                dados["status"] = "ativo"

    def _minerador_disponivel(self, minerador_id):
        dados = self.mineradores.get(minerador_id)
        if not dados or not dados.get("conexao"):
            return False
        punido_ate = dados.get("punido_ate", 0)
        return not punido_ate or punido_ate <= time.time()

    def _escolher_minerador_ataque(self):
        candidatos = [
            (minerador_id, dados)
            for minerador_id, dados in self.mineradores.items()
            if dados.get("conexao")
        ]
        if not candidatos:
            return None
        candidatos.sort(
            key=lambda item: (
                item[1].get("blocos_resolvidos", 0),
                item[1].get("consecutivos", 0),
                item[0],
            ),
            reverse=True,
        )
        return candidatos[0][0]

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
            "ataque_alvo": minerador_id == self.minerador_ataque,
        }

    def estado_publico(self):
        with self.lock:
            self._liberar_punicoes_expiradas()
            return {
                "mineradores": {
                    minerador_id: self._estado_minerador_publico(minerador_id, dados)
                    for minerador_id, dados in self.mineradores.items()
                },
                "ataque": {
                    "ativo": self.ataque_ativo,
                    "minerador_alvo": self.minerador_ataque,
                    "tipo": "51%",
                },
                "blocos_minerados": list(self.historico_blocos),
                "bloco_atual_resolvido": self.bloco_atual_resolvido,
                "mineradores_conectados": len([d for d in self.mineradores.values() if d.get("conexao")]),
            }

    def simular_ataque(self, minerador_alvo=None):
        with self.lock:
            self._liberar_punicoes_expiradas()

            alvo = minerador_alvo if minerador_alvo in self.mineradores else None
            if alvo is None:
                alvo = self._escolher_minerador_ataque()

            if alvo is None:
                return {"ok": False, "mensagem": "Nenhum minerador conectado para simular o ataque."}

            self.ataque_ativo = True
            self.minerador_ataque = alvo
            return {
                "ok": True,
                "mensagem": f"Ataque 51% ativado em {alvo}.",
                "ataque": {
                    "ativo": self.ataque_ativo,
                    "minerador_alvo": self.minerador_ataque,
                    "tipo": "51%",
                },
                "mineradores": {
                    minerador_id: self._estado_minerador_publico(minerador_id, dados)
                    for minerador_id, dados in self.mineradores.items()
                },
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
                }
            )
            self.mineradores[minerador_id] = dados
            print(f"[CONEXÃO] Minerador registrado: {minerador_id} ({endereco})")

    def remover_minerador(self, minerador_id):
        with self.lock:
            dados = self.mineradores.pop(minerador_id, None)
            if dados:
                print(f"[CONEXÃO] Minerador removido: {minerador_id}")
                if self.minerador_ataque == minerador_id:
                    self.minerador_ataque = None

    def gerenciar_minerador(self, conexao, endereco):
        minerador_id = None
        print(f"[CONEXÃO] Novo minerador: {endereco}")

        buffer = ""
        try:
            while True:
                dados = conexao.recv(4096).decode()
                if not dados: break
                
                buffer += dados
                while "\n" in buffer:
                    msg, buffer = buffer.split("\n", 1)
                    if not msg.strip(): continue
                    
                    resposta = json.loads(msg)
                    if resposta.get("tipo") == "hello" or not minerador_id:
                        minerador_id = resposta.get("minerador", minerador_id or f"{endereco[0]}:{endereco[1]}")
                        self.registrar_minerador(conexao, endereco, minerador_id)
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
            indice_recebido = resposta['indice']
            indice_esperado = len(self.blockchain.chain)
            dados_minerador = self.mineradores.get(minerador_id)

            if not dados_minerador:
                return

            if dados_minerador.get("punido_ate", 0) > time.time():
                print(f"[PUNIÇÃO] {minerador_id} tentou validar bloco durante o bloqueio.")
                return

            if indice_recebido == indice_esperado and not self.bloco_atual_resolvido:
                self.bloco_atual_resolvido = True
                
                novo = Bloco(indice_recebido, resposta['dados'], self.blockchain.ultimo_bloco().hash)
                novo.nonce = resposta['nonce']
                novo.hash = resposta['hash']
                
                self.blockchain.chain.append(novo)
                self.historico_blocos.append(
                    {
                        "indice": indice_recebido,
                        "minerador": minerador_id,
                        "nonce": resposta.get("nonce"),
                        "hash": resposta.get("hash", "")[:16],
                        "timestamp": datetime.now().isoformat(),
                    }
                )

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
                
                print(f"\n" + "!"*50)
                print(f"VENCEDOR: {minerador_id} | {endereco}")
                print(f"Bloco #{indice_recebido} validado e inserido!")
                print("!"*50)
                
                self.blockchain.exibir_blockchain()

    def gerador_de_desafios(self):
        nomes = ["Lukas", "Maria", "Carlos", "Ana", "Bruno", "Faculdade_TI"]
        docs = ["Contrato_Social", "Escritura_Terreno", "Diploma_Digital", "Nota_Fiscal"]

        while True:
            time.sleep(5) 

            # Só gera novo desafio se houver mineradores e o anterior foi resolvido
            with self.lock:
                self._liberar_punicoes_expiradas()
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
                proximo_indice = len(self.blockchain.chain)
                
                autor = random.choice(nomes)
                tipo = random.choice(docs)
                hash_fake = f"sha256_{random.getrandbits(64):016x}"
                
                # --- ASSINATURA DIGITAL ---
                # O servidor assina o hash do documento para provar que ele é o emissor
                assinatura_digital = assinar_dados(self.chave_privada, hash_fake)
                
                # Criamos um dicionário robusto de dados
                dados_payload = {
                    "documento": tipo,
                    "autor_nome": autor,
                    "hash_arquivo": hash_fake,
                    "assinatura_emissor": assinatura_digital,
                    "chave_publica_emissor": self.chave_publica_pem
                }
                # --------------------------------------

                # Prepara o pacote usando o método da Blockchain
                # Note que passamos o payload como string JSON para os 'dados' do bloco
                tarefa = self.blockchain.preparar_novo_bloco(hash_fake, json.dumps(dados_payload))
                tarefa['indice'] = proximo_indice
                
                self.bloco_atual_resolvido = False
                mensagem = (json.dumps(tarefa) + "\n").encode()

                if self.ataque_ativo and self.minerador_ataque in mineradores_ativos:
                    destinatarios = [self.minerador_ataque]
                else:
                    destinatarios = list(mineradores_ativos.keys())

                print(f"\n[SISTEMA] Documento Assinado! Disparando Bloco #{proximo_indice}...")
                
                for minerador_id in destinatarios:
                    dados_minerador = mineradores_ativos.get(minerador_id)
                    if not dados_minerador:
                        continue
                    try:
                        dados_minerador["conexao"].sendall(mensagem)
                    except:
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

        print("\n" + "="*50)
        print(" SERVIDOR BLOCKCHAIN COM ASSINATURA RSA ")
        print(f" Chave Pública: {self.chave_publica_pem[:50]}...")
        print(f" Host: {self.host} | Porta: {self.porta} | Controle HTTP: {self.porta_controle}")
        print("="*50)

        while True:
            conn, addr = servidor.accept()
            t = threading.Thread(target=self.gerenciar_minerador, args=(conn, addr), daemon=True)
            t.start()

@servidor_app.route("/api/estado")
def api_estado_controle():
    if servidor_instancia is None:
        return jsonify({"erro": "Servidor ainda inicializando."}), 503
    return jsonify(servidor_instancia.estado_publico())


@servidor_app.route("/api/ataque", methods=["POST"])
def api_simular_ataque():
    if servidor_instancia is None:
        return jsonify({"ok": False, "mensagem": "Servidor ainda inicializando."}), 503

    dados = request.get_json(silent=True) or {}
    resultado = servidor_instancia.simular_ataque(dados.get("minerador"))
    codigo = 200 if resultado.get("ok") else 400
    return jsonify(resultado), codigo


if __name__ == "__main__":
    s = ServidorBlockchain()
    s.iniciar()