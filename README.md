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
- [Validação dos Documentos e Envio](#validação-dos-documentos-e-envio)
- [Benefícios da Blockchain para Documentos](#benefícios-da-blockchain-para-documentos)
- [Recursos Principais](#recursos-principais)

---

## 🎯 Visão Geral

Este projeto implementa um sistema de **blockchain descentralizado** para registro de documentos digitais. O sistema utiliza:

- **Prova de Trabalho (Proof of Work)**: Um mecanismo de consenso baseado em cálculos de hash
- **Assinatura Digital RSA**: Para autenticação e integridade dos documentos
- **Mineração Distribuída**: Múltiplos mineradores competem para resolver blocos
- **Regra da Maior Cadeia**: A cadeia válida é a do minerador com maior comprimento reportado
- **Validação pelos Mineradores**: Os próprios mineradores validam e atualizam suas cadeias locais
- **Rede Cliente-Servidor**: Arquitetura baseada em sockets TCP/IP

O objetivo principal é demonstrar como documentos podem ser registrados de forma imutável e verificável em uma rede descentralizada.

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────┐
│         SERVIDOR BLOCKCHAIN (servidor.py)           │
│  • Simula os orgãos emissores                       │
│  • Envia os blocos para serem minerados             │
│  • Atualiza a interface gráfica                     │
└─────────────────────────────────────────────────────┘
          ▲                  ▲                  ▲
          │                  │                  │
          |                  |                  |
          │                  │                  │
┌─────────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ MINERADOR 1         │ │ MINERADOR 2     │ │ MINERADOR N     │
│ (minerador.py)      │ │ (minerador.py)  │ │ (minerador.py)  │
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
Coordena os mineradores e aplica a regra da maior cadeia.

**Classes:**
- `ServidorBlockchain()` - Servidor central

**Funcionalidades:**
- Gera desafios de mineração a cada 5 segundos
- Mantém lista de mineradores conectados
- Aguarda um pool mínimo de mineradores conectados antes de iniciar desafios
- Usa a maior cadeia reportada pelos mineradores como referência válida
- Não precisa armazenar a cadeia completa de blocos
- Assina digitalmente cada documento com a chave da entidade emissora
- Gerencia threads para cada minerador

**Componentes:**
1. **Gerador de Desafios**: Cria novos blocos periodicamente
2. **Pool de Mineradores**: Gerencia múltiplas conexões simultâneas
3. **Consenso de Maior Cadeia**: Atualiza a referência com base nos estados enviados pelos mineradores
4. **Sistema de Assinatura**: Usa chaves privadas exclusivas por entidade emissora

---

## 🚀 Como Executar

### Pré-requisitos
- Docker instalado
- Docker Compose instalado

Este projeto está configurado para execução apenas com Docker Compose.

## 🐳 Como Executar com Docker Compose

Execute o projeto somente com Docker Compose:

```bash
docker compose up --build
```

Depois acesse a interface gráfica em:

```
http://localhost:8080
```

Para encerrar tudo:

```bash
docker compose down
```

### O que o compose sobe
- Zookeeper
- Kafka
- Servidor blockchain
- 6 mineradores
- Monitor web em tempo real

### Rede interna
- Servidor: `blockchain-servidor:5000`
- Controle do servidor: `blockchain-servidor:5001`
- Kafka: `kafka:9092`

---

## Interface Gráfica de Monitoramento

O projeto inclui um **monitor web em tempo real** que mostra:
- **Mineradores ativos** com indicadores visuais
- **Placar de blocos** minerados por cada minerador
- **Blocos minerados** com disseminação via Kafka em tempo real
- **Status de conexão** com servidor e Kafka

### Acessando o Monitor

Quando rodar o Docker Compose, o monitor estará disponível em:

```
http://localhost:8080
```

### Recursos do Monitor

1. **Seção de Mineradores Ativos**
   - Mostra lista de mineradores conectados
   - Exibe contador de blocos resolvidos por minerador
   - Status de atividade com animação em tempo real

2. **Placar de Blocos**
   - Ranking dos mineradores por número de blocos resolvidos
   - Atualização em tempo real via WebSocket

3. **Histórico de Blocos Minerados**
   - Mostra os blocos minerados com foco em **índice do bloco** e **minerador vencedor**
   - Mantém o histórico em ordem visual para acompanhar os vencedores ao longo do tempo

4. **Indicadores Visuais**
   - Animação de **cadeia em crescimento** com os blocos interligados
   - A cadeia exibe todos os blocos disponíveis no monitor 
   - Animação de disseminação do minerador vencedor para os demais mineradores
   - Efeito de pulso em mineradores ativos e destaque visual do vencedor

### Como o Monitor Funciona Internamente

1. **Conexão Kafka**: O monitor escuta o tópico `blocos_minerados` em tempo real
2. **WebSocket**: Usa Socket.IO para comunicação bidirecional com o navegador
3. **Dashboard Reativo**: Interface atualiza instantaneamente quando blocos são minerados
4. **Disseminação Visual**: Mostra claramente qual minerador conseguiu minerar primeiro
5. **Sincronização com Servidor**: O monitor mescla o estado oficial de blocos para não perder o bloco #1

---

## 🔄 Fluxo de Funcionamento

### Sequência de Eventos

```
1. INICIALIZAÇÃO
   ├─ Servidor inicia e gera pares de chaves RSA para emissores oficiais
   ├─ Cadeias locais dos mineradores começam no bloco Gênesis
   └─ Gerador de desafios inicia (thread daemon)

2. CONEXÃO DE MINERADORES
   ├─ Minerador 1 conecta → reconhecimento do servidor
   ├─ Minerador 2 conecta → reconhecimento do servidor
   ├─ Minerador 3 conecta → reconhecimento do servidor
   ├─ Minerador 4 conecta → reconhecimento do servidor
   ├─ Minerador 5 conecta → reconhecimento do servidor
   └─ Minerador 6 conecta → reconhecimento do servidor

3. GERAÇÃO DE DESAFIO (a cada 5 segundos)
   ├─ Servidor aguarda o mínimo de 6 mineradores conectados
   ├─ Servidor seleciona entidade emissora e documento aleatório
   ├─ Gera hash SHA-256 simulado
   ├─ Assina digitalmente com RSA (chave privada da entidade)
   ├─ Encapsula em JSON
   └─ Envia para todos os mineradores

4. MINERAÇÃO DISTRIBUÍDA
   ├─ Minerador 1: Inicia PoW (cálculo de hash)
   ├─ Minerador 2: Inicia PoW (concorrência)
   ├─ Minerador 3: Inicia PoW (concorrência)
   ├─ Minerador 4: Inicia PoW (concorrência)
   ├─ Minerador 5: Inicia PoW (concorrência)
   ├─ Minerador 6: Inicia PoW (concorrência)
   └─ O primeiro a encontrar hash válido vence

5. VALIDAÇÃO E CONSENSO
   ├─ Mineradores validam e anexam blocos em suas cadeias locais
   ├─ Mineradores reportam tamanho/hash da cadeia ao servidor
   ├─ Servidor adota a maior cadeia como referência válida
   └─ Retorna ao passo 3

6. BLOQUEIO DE CÓPIAS SIMULTÂNEAS
   ├─ Lock mutex garante que apenas um bloco válido
   ├─ Impede duplicações na cadeia
   └─ Garante consenso distribuído
```

---

## ✅ Validação dos Documentos e Envio

Nesta simulação, os documentos são considerados válidos quando passam pelo emissor oficial e chegam assinados digitalmente para a etapa de mineração.

### Órgãos emissores autorizados

- Cartório Lucena
- Cartório Marques
- Cartório Barreto
- Segurança Pública do RN
- Governo Federal

Cada órgão possui seu próprio par de chaves RSA.

- **Chave privada do órgão**: usada para assinar o hash do documento.
- **Chave pública do órgão**: enviada no payload para permitir verificação da assinatura.

### Passo a passo do fluxo

1. O servidor seleciona um órgão emissor autorizado.
2. O servidor gera os dados do documento (tipo, autor, hash do arquivo).
3. O órgão emissor assina o hash do documento com sua chave privada exclusiva.
4. O payload do bloco inclui:
   - Tipo de documento
   - Autor do documento
   - Órgão emissor
   - Hash do arquivo
   - Assinatura digital do emissor
   - Chave pública do emissor
5. Esse payload é enviado como desafio para os mineradores.
6. O primeiro minerador que resolve o PoW envia o bloco ao servidor.
7. O servidor valida o bloco recebido e atualiza a cadeia de referência pela regra da maior cadeia para atualizar o monitor blockchain na página HTML, apenas para fins de ver a cadeia crescendo.

### Resultado prático

- O documento entra na blockchain com rastreabilidade de origem (qual órgão assinou).
- A assinatura digital protege autenticidade e integridade dos dados.
- Sem a chave privada correta do órgão, não é possível gerar assinatura legítima.

---

## 🌍 Benefícios da Blockchain para Documentos

Aplicar blockchain ao registro de imóveis e documentos resolve problemas clássicos de confiança, fraude e burocracia. No contexto deste projeto (órgão emissor assinando documento com RSA e envio para mineração), os principais benefícios são:

### 1. Imutabilidade e prevenção de fraudes

Após o registro em bloco validado, qualquer alteração no documento muda o hash e invalida o encadeamento da cadeia.

- Isso dificulta adulteração de dados históricos de propriedade.
- Uma tentativa de alterar um bloco antigo quebra a consistência esperada pelos nós.

### 2. Autenticidade e não-repúdio com RSA

Cada órgão emissor assina o hash do documento com sua chave privada exclusiva.

- A validação é feita com a chave pública correspondente.
- O emissor não pode negar a emissão legítima do documento assinado.
- Terceiros não conseguem forjar assinatura sem a chave privada do órgão.

### 3. Eliminação de ponto único de falha

Com a rede distribuída de mineradores e nós, o histórico não depende de um único servidor local.

- Quedas pontuais de um componente não apagam o histórico já disseminado.
- O sistema mantém maior resiliência operacional comparado a um registro centralizado único.

### 4. Transparência e auditoria rápida

Com os dados de bloco (ou hashes) e assinaturas disponíveis, a validação pode ser automatizada.

- Scripts e sistemas conseguem checar integridade e assinatura em segundos.
- Auditorias ficam mais objetivas, rastreáveis e com menor dependência de validação manual.

### 5. Prevenção de conflito de estado (ex.: venda dupla)

O consenso e a ordem de inclusão dos blocos reduzem conflitos de registro simultâneo sobre o mesmo ativo.

- A transação confirmada primeiro passa a representar o estado válido da rede.
- Tentativas conflitantes posteriores podem ser detectadas e rejeitadas pelas regras de validação.

---

## ⚙️ Recursos Principais

### 1. **Prova de Trabalho (Proof of Work)**
- Dificuldade ajustável (padrão: 5 zeros iniciais)
- Aumentar dificuldade = mais poder computacional necessário
- Diminuir dificuldade = blocos mais rápidos

### 2. **Assinatura Digital RSA**
- Cada documento é assinado com chave privada exclusiva da entidade emissora
- Entidades emissoras: Cartório Lucena, Cartório Marques, Cartório Barreto, Segurança Pública do RN e Governo Federal
- Chave pública incluída no bloco para verificação
- Impossível forjar sem a chave privada

### 3. **Mineração Distribuída**
- Múltiplos mineradores competem simultaneamente
- O primeiro a resolver adiciona o bloco
- Recompensa implícita: segurança da rede

### 4. **Regra da Maior Cadeia**
- O servidor não mantém a cadeia completa local como fonte de verdade
- Cada minerador mantém sua cadeia local e envia status (`cadeia_tamanho` e `ultimo_hash`)
- A cadeia com maior comprimento é considerada válida

### 5. **Validação de Integridade**
```python
# Cada minerador valida:
✓ Se o hash de cada bloco está correto
✓ Se cada bloco aponta para o anterior correto
✓ Se a cadeia não foi modificada
```
---

## 📊 Dados de um Bloco

Exemplo de estrutura JSON de um bloco:

```json
{
  "indice": 1,
  "timestamp": 1684756234.5678,
  "dados": {
    "documento": "Contrato_Social",
      "entidade_emissora": "Cartório Lucena",
      "autor_nome": "Cartório Lucena",
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

## 👨‍💻 Autor e Contexto

**Projeto**: Sistema de Blockchain Distribuído com Assinatura Digital  
**Propósito**: Educacional - Demonstração de conceitos de sistemas distribuídos  
**Tecnologia**: Sistemas Distribuídos e Criptografia  
**Data**: Março de 2026  
**Autores**: Diego Rabelo, Lucas Marques e Nilton Barreto  
**Professor**: Eduardo Galvão Lucena  
**Disciplina**: Sistemas Distribuídos - DCA3704
