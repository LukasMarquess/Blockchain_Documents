# 🔗 Sistema de Blockchain com Prova de Trabalho Distribuída

Um projeto educacional que implementa uma blockchain funcional com um sistema de mineração distribuída e assinatura digital RSA. O projeto demonstra conceitos de sistemas distribuídos, criptografia e consenso descentralizado.

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura do Sistema](#arquitetura-do-sistema)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Módulos do Projeto](#módulos-do-projeto)
- [Como Executar](#como-executar)
- [Fluxo de Funcionamento](#fluxo-de-funcionamento)
- [Recursos Principais](#recursos-principais)

---

## 🎯 Visão Geral

Este projeto implementa um sistema de **blockchain descentralizado** para registro de documentos digitais. O sistema utiliza:

- **Prova de Trabalho (Proof of Work)**: Um mecanismo de consenso baseado em cálculos de hash
- **Assinatura Digital RSA**: Para autenticação e integridade dos documentos
- **Mineração Distribuída**: Múltiplos mineradores competem para resolver blocos
- **Rede Cliente-Servidor**: Arquitetura baseada em sockets TCP/IP

O objetivo principal é demonstrar como documentos podem ser registrados de forma imutável e verificável em uma rede descentralizada.

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────┐
│         SERVIDOR BLOCKCHAIN (servidor.py)          │
│  • Gerencia blockchain central                      │
│  • Gera desafios de mineração                       │
│  • Assinatura digital RSA                           │
│  • Valida blocos resolvidos                         │
└─────────────────────────────────────────────────────┘
          ▲                  ▲                  ▲
          │                  │                  │
    TCP/IP Port 5000    TCP/IP Port 5000   TCP/IP Port 5000
          │                  │                  │
┌─────────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ MINERADOR 1         │ │ MINERADOR 2     │ │ MINERADOR N     │
│ (minerador.py)      │ │ (minerador.py)  │ │ (minerador.py)  │
│ • Prova de Trabalho │ │ • Competição    │ │ • Threads       │
└─────────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 💻 Tecnologias Utilizadas

### Linguagem
- **Python 3.8+** - Linguagem principal do projeto

### Bibliotecas Implementadas

| Biblioteca | Propósito |
|-----------|-----------|
| `socket` | Comunicação TCP/IP entre servidor e mineradores |
| `threading` | Execução concorrente de múltiplos mineradores |
| `hashlib` | Algoritmo SHA-256 para geração de hashes |
| `json` | Serialização de dados entre cliente e servidor |
| `cryptography` | Criptografia RSA (geração, assinatura e verificação) |
| `time` | Timestamps e controle de tempo |

### Conceitos Criptográficos
- **SHA-256**: Função hash criptográfica para integridade dos blocos
- **RSA-2048**: Assinatura digital assimétrica para autenticação
- **Proof of Work**: Mecanismo de consenso com dificuldade ajustável

---

## 📦 Módulos do Projeto

### 1. **blockchain.py** - Gerenciador da Cadeia de Blocos
Responsável por gerenciar a estrutura completa da blockchain.

**Classes:**
- `Blockchain()` - Gerencia toda a cadeia de blocos

**Funcionalidades Principais:**
- Criação do bloco Gênesis (primeiro bloco)
- Validação da integridade da cadeia
- Preparação de novos blocos para mineração
- Exibição formatada do estado atual da blockchain

**Atributos:**
- `chain`: Lista de blocos
- `dificuldade`: Nível de dificuldade (número de zeros iniciais no hash)

---

### 2. **bloco.py** - Estrutura de Blocos
Define a estrutura individual de cada bloco na blockchain.

**Classes:**
- `Bloco()` - Representa um bloco individual

**Funcionamento:**
- Cada bloco contém: índice, timestamp, dados, hash anterior e nonce
- **Nonce**: Número aleatório ajustado durante a mineração
- **Hash**: SHA-256 calculado a partir de todos os dados do bloco

**Método Principal:**
- `minerar_bloco(dificuldade)` - Executa Proof of Work até encontrar um hash válido

**Exemplo de Prova de Trabalho:**
```
Dificuldade = 5 significa encontrar um hash que comece com "00000"
Exemplo de hash válido: 00000abc123def456...
```

---

### 3. **identidade.py** - Criptografia RSA
Implementa assinatura digital e gerenciamento de chaves.

**Funções:**

| Função | Descrição |
|--------|-----------|
| `gerar_chaves()` | Gera par de chaves RSA-2048 |
| `assinar_dados()` | Assina dados com chave privada |
| `exportar_chave_publica()` | Converte chave pública para formato PEM (string) |

**Algoritmo de Assinatura:**
- Padding: PSS (Probabilistic Signature Scheme)
- Hash: SHA-256
- Tamanho da chave: 2048 bits

---

### 4. **minerador.py** - Cliente Minerador Distribuído
Conecta-se ao servidor e executa a prova de trabalho.

**Características:**
- Conexão TCP/IP ao servidor (porta 5000)
- Recebe desafios de mineração em tempo real
- Executa Proof of Work em thread separada
- Envia solução ao servidor assim que encontrada
- Suporta múltiplas instâncias simultâneas

**Fluxo de Operação:**
1. Conecta ao servidor
2. Aguarda receber desafios
3. Calcula hashes iterativamente (nonce incrementado)
4. Quando encontra hash válido, envia resposta
5. Retorna para aguardar novo desafio

---

### 5. **servidor.py** - Servidor Central da Blockchain
Gerencia a blockchain, valida blocos e coordena mineradores.

**Classes:**
- `ServidorBlockchain()` - Servidor central

**Funcionalidades:**
- Gera desafios de mineração a cada 5 segundos
- Mantém lista de mineradores conectados
- Valida blocos resolvidos
- Assina digitalmente cada documento
- Gerencia threads para cada minerador

**Componentes:**
1. **Gerador de Desafios**: Cria novos blocos periodicamente
2. **Pool de Mineradores**: Gerencia múltiplas conexões simultâneas
3. **Validador**: Verifica soluções antes de adicionar à cadeia
4. **Sistema de Assinatura**: Assina cada documento com chave privada RSA

---

## 🚀 Como Executar

### Pré-requisitos
```bash
# Instalar a biblioteca de criptografia
pip install cryptography
```

### Passo 1: Iniciar o Servidor
Abra um terminal e execute:
```bash
python servidor.py
```

**Saída esperada:**
```
==================================================
 SERVIDOR BLOCKCHAIN COM ASSINATURA RSA 
 Chave Pública: -----BEGIN PUBLIC KEY-----...
==================================================
```

### Passo 2: Iniciar Mineradores
Em terminais separados, execute (para cada minerador):
```bash
# Terminal 1
python minerador.py

# Terminal 2
python minerador.py

# Terminal 3
python minerador.py
```

**Saída esperada (minerador):**
```
========================================
 MINERADOR CONECTADO E COMPETINDO 
========================================
[REDE] Recebido desafio para Bloco 1
[TRABALHO] Iniciando mineração do Bloco 1...
[SUCESSO] Bloco 1 resolvido com Nonce 12345!
```

### Exemplo de Execução Completa
```
Terminal 1 (Servidor):
==================================================
[SISTEMA] Documento Assinado! Disparando Bloco #1...
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
VENCEDOR: ('127.0.0.1', 54321)
Bloco #1 validado e inserido!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Terminal 2 (Minerador 1):
[SUCESSO] Bloco 1 resolvido com Nonce 89456!

Terminal 3 (Minerador 2):
[CANCELADO] Bloco 1 já foi resolvido. Parando...
```

---

## 🔄 Fluxo de Funcionamento

### Sequência de Eventos

```
1. INICIALIZAÇÃO
   ├─ Servidor inicia e gera par de chaves RSA
   ├─ Blockchain criada com bloco Gênesis
   └─ Gerador de desafios inicia (thread daemon)

2. CONEXÃO DE MINERADORES
   ├─ Minerador 1 conecta → reconhecimento do servidor
   ├─ Minerador 2 conecta → reconhecimento do servidor
   └─ Minerador N conecta → reconhecimento do servidor

3. GERAÇÃO DE DESAFIO (a cada 5 segundos)
   ├─ Servidor seleciona autor e documento aleatório
   ├─ Gera hash SHA-256 simulado
   ├─ Assina digitalmente com RSA (chave privada)
   ├─ Encapsula em JSON
   └─ Envia para todos os mineradores

4. MINERAÇÃO DISTRIBUÍDA
   ├─ Minerador 1: Inicia PoW (cálculo de hash)
   ├─ Minerador 2: Inicia PoW (concorrência)
   ├─ Minerador 3: Inicia PoW (concorrência)
   ├─ Minerador 4: Inicia PoW (concorrência)
   └─ O primeiro a encontrar hash válido vence

5. VALIDAÇÃO E CONSENSO
   ├─ Servidor valida solução
   ├─ Adiciona bloco à blockchain
   ├─ Transmite novo estado para mineradores
   └─ Retorna ao passo 3

6. BLOQUEIO DE CÓPIAS SIMULTÂNEAS
   ├─ Lock mutex garante que apenas um bloco válido
   ├─ Impede duplicações na cadeia
   └─ Garante consenso distribuído
```

---

## ⚙️ Recursos Principais

### 1. **Prova de Trabalho (Proof of Work)**
- Dificuldade ajustável (padrão: 5 zeros iniciais)
- Aumentar dificuldade = mais poder computacional necessário
- Diminuir dificuldade = blocos mais rápidos

### 2. **Assinatura Digital RSA**
- Cada documento é assinado com chave privada do servidor
- Chave pública incluída no bloco para verificação
- Impossível forjar sem a chave privada

### 3. **Mineração Distribuída**
- Múltiplos mineradores competem simultaneamente
- O primeiro a resolver adiciona o bloco
- Recompensa implícita: segurança da rede

### 4. **Validação de Integridade**
```python
# A blockchain valida:
✓ Se o hash de cada bloco está correto
✓ Se cada bloco aponta para o anterior correto
✓ Se a cadeia não foi modificada
```

### 5. **Thread-Safety**
- Lock mutex (`threading.Lock`) garante consistência
- Previne condições de corrida
- Apenas uma transação modificando blockchain por vez

---

## 📊 Dados de um Bloco

Exemplo de estrutura JSON de um bloco:

```json
{
  "indice": 1,
  "timestamp": 1684756234.5678,
  "dados": {
    "documento": "Contrato_Social",
    "autor_nome": "Lukas",
    "hash_arquivo": "sha256_a1b2c3d4e5f6g7h8",
    "assinatura_emissor": "0x1a2b3c4d5e6f...",
    "chave_publica_emissor": "-----BEGIN PUBLIC KEY-----..."
  },
  "hash_anterior": "00000abc123def...",
  "nonce": 89456,
  "hash": "00000xyz789abc..."
}
```

---

## 🔒 Segurança Implementada

| Mecanismo | Função |
|-----------|--------|
| **SHA-256** | Garante integridade dos blocos |
| **RSA-2048** | Autentica origem dos documentos |
| **Proof of Work** | Torna ataques computacionalmente caros |
| **Thread Locks** | Previne race conditions |
| **Chain Validation** | Detecta modificações na cadeia |

---

## 📈 Possíveis Melhorias Futuras

- [ ] Implementar merkle tree para múltiplas transações por bloco
- [ ] Sistema de recompensas para mineradores
- [ ] Contratos inteligentes (smart contracts)
- [ ] Interface web para visualização da blockchain
- [ ] Persistência em banco de dados
- [ ] Algoritmo de consenso PoS (Proof of Stake)
- [ ] Criptografia end-to-end entre nós
- [ ] Sistema de permissões e controle de acesso

---

## 👨‍💻 Autor e Contexto

**Projeto**: Sistema de Blockchain Distribuído com Assinatura Digital
**Propósito**: Educacional - Demonstração de conceitos de sistemas distribuídos
**Tecnologia**: Sistemas Distribuídos e Criptografia
**Data**: Março de 2026

---

## 📝 Licença

Este projeto é educacional e está disponível para fins de aprendizado.

---

## ❓ FAQ

**P: Por que o minerador às vezes não consegue resolver um bloco?**
R: A dificuldade pode ser ajustada em `blockchain.py` na variável `self.dificuldade`. Aumentar esse valor requer mais poder computacional.

**P: Como aumentar o número de mineradores?**
R: Simplesmente execute mais instâncias de `python minerador.py` em terminais diferentes.

**P: O que acontece se o servidor cair?**
R: Os mineradores tentarão reconectar infinitamente. Reinicie o servidor e eles se reconectarão automaticamente.

**P: Os dados são persistentes?**
R: Não. Quando o servidor é encerrado, toda a blockchain é perdida. Para persistência, seria necessário implementar um banco de dados.

**P: Como verificar se um documento é legítimo?**
R: Você pode verificar a assinatura RSA usando a chave pública armazenada no bloco.

---

## 📚 Referências Conceituais

- Nakamoto, S. (2008). Bitcoin: A Peer-to-Peer Electronic Cash System
- Schneier, B. (1996). Applied Cryptography
- NIST. Federal Information Processing Standards (FIPS 186-4)

---

