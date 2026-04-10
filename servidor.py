import socket
import json
import threading
import random
import time
import os
from blockchain import Blockchain
from bloco import Bloco
from identidade import gerar_chaves, assinar_dados, exportar_chave_publica

class ServidorBlockchain:
    def __init__(self):
        self.host = os.getenv("SERVER_HOST", "0.0.0.0")
        self.porta = int(os.getenv("SERVER_PORT", "5000"))
        self.blockchain = Blockchain()
        self.mineradores = []
        self.bloco_atual_resolvido = True # Começa como True para o gerador iniciar
        self.lock = threading.Lock()

        # --- IDENTIDADE DO SERVIDOR ---
        # O servidor gera seu par de chaves ao iniciar
        self.chave_privada, self.chave_publica = gerar_chaves()
        # Exportamos a pública para formato PEM (string) para enviar via JSON
        self.chave_publica_pem = exportar_chave_publica(self.chave_publica)
        # ------------------------------------------

    def gerenciar_minerador(self, conexao, endereco):
        self.mineradores.append(conexao)
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
                    self.processar_vitoria(resposta, endereco)
        except Exception:
            pass
        finally:
            if conexao in self.mineradores:
                self.mineradores.remove(conexao)
            conexao.close()

    def processar_vitoria(self, resposta, endereco):
        with self.lock:
            indice_recebido = resposta['indice']
            indice_esperado = len(self.blockchain.chain)

            if indice_recebido == indice_esperado and not self.bloco_atual_resolvido:
                self.bloco_atual_resolvido = True
                
                novo = Bloco(indice_recebido, resposta['dados'], self.blockchain.ultimo_bloco().hash)
                novo.nonce = resposta['nonce']
                novo.hash = resposta['hash']
                
                self.blockchain.chain.append(novo)
                
                print(f"\n" + "!"*50)
                print(f"VENCEDOR: {endereco}")
                print(f"Bloco #{indice_recebido} validado e inserido!")
                print("!"*50)
                
                self.blockchain.exibir_blockchain()

    def gerador_de_desafios(self):
        nomes = ["Lukas", "Maria", "Carlos", "Ana", "Bruno", "Faculdade_TI"]
        docs = ["Contrato_Social", "Escritura_Terreno", "Diploma_Digital", "Nota_Fiscal"]

        while True:
            time.sleep(5) 

            # Só gera novo desafio se houver mineradores e o anterior foi resolvido
            if len(self.mineradores) > 0 and self.bloco_atual_resolvido:
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

                print(f"\n[SISTEMA] Documento Assinado! Disparando Bloco #{proximo_indice}...")
                
                for m in self.mineradores[:]:
                    try:
                        m.sendall(mensagem)
                    except:
                        self.mineradores.remove(m)

    def iniciar(self):
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((self.host, self.porta))
        servidor.listen(10)

        threading.Thread(target=self.gerador_de_desafios, daemon=True).start()

        print("\n" + "="*50)
        print(" SERVIDOR BLOCKCHAIN COM ASSINATURA RSA ")
        print(f" Chave Pública: {self.chave_publica_pem[:50]}...")
        print(f" Host: {self.host} | Porta: {self.porta}")
        print("="*50)

        while True:
            conn, addr = servidor.accept()
            t = threading.Thread(target=self.gerenciar_minerador, args=(conn, addr), daemon=True)
            t.start()

if __name__ == "__main__":
    s = ServidorBlockchain()
    s.iniciar()