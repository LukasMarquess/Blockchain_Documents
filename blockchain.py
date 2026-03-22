import json
import time
from bloco import Bloco 

class Blockchain:
    def __init__(self):
        self.chain = []
        self.dificuldade = 5  # Ajuste conforme a potência do seu PC
        self.criar_bloco_genesis()

    def criar_bloco_genesis(self):
        bloco_genesis = Bloco(0, "Bloco Gênesis - Sistema de Documentos", "0")
        bloco_genesis.minerar_bloco(self.dificuldade)
        self.chain.append(bloco_genesis)

    def ultimo_bloco(self):
        return self.chain[-1]

    # --- PREPARAR DADOS PARA MINERAÇÃO ---
    def preparar_novo_bloco(self, hash_documento, autor):
        """Prepara os dados para enviar ao minerador via rede."""
        dados_registro = {
            "hash_arquivo": hash_documento,
            "autor": autor,
            "data_registro": time.ctime()
        }
        
        return {
            "indice": len(self.chain),
            "dados": json.dumps(dados_registro),
            "hash_anterior": self.ultimo_bloco().hash,
            "dificuldade": self.dificuldade
        }
    # -------------------------------------------

    def validar_corrente(self):
        for i in range(1, len(self.chain)):
            atual = self.chain[i]
            anterior = self.chain[i-1]
            if atual.hash != atual.calcular_hash():
                return False
            if atual.hash_anterior != anterior.hash:
                return False
        return True

    def exibir_blockchain(self):
        print("\n" + "="*60)
        print("ESTADO ATUAL DA BLOCKCHAIN")
        print("="*60)
        for bloco in self.chain:
            print(f"Bloco: {bloco.indice} | Hash: {bloco.hash[:15]}...")
            print(f"Conteúdo: {bloco.dados}")
            print("-" * 60)