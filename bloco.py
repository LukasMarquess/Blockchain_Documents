import hashlib
import time

class Bloco:
    def __init__(self, indice, dados, hash_anterior):
        self.indice = indice
        self.timestamp = time.time()
        self.dados = dados  # Aqui guardamos o JSON com Hash do arquivo + Autor
        self.hash_anterior = hash_anterior
        self.nonce = 0
        self.hash = self.calcular_hash()

    def calcular_hash(self):
        # O hash é gerado combinando todos os dados do bloco
        conteudo = f"{self.indice}{self.timestamp}{self.dados}{self.hash_anterior}{self.nonce}"
        return hashlib.sha256(conteudo.encode()).hexdigest()

    def minerar_bloco(self, dificuldade):
        # Prova de Trabalho: encontra um hash que comece com N zeros
        print(f"Minerando bloco {self.indice}...", end=" ")
        while self.hash[:dificuldade] != "0" * dificuldade:
            self.nonce += 1
            self.hash = self.calcular_hash()
        print(f"Sucesso! Hash: {self.hash}")