# Guia Rapido - Rodando o Projeto

## Modo unico: Docker Compose

### Pre-requisitos
- Docker instalado
- Docker Compose instalado

### Executar
```bash
docker compose up --build
```

### Ver logs em tempo real
```bash
docker compose logs -f
```

### Acessar monitor
http://localhost:8080

### Regras atuais do sistema
- Mineracao inicia quando 6 mineradores estao conectados
- Punicao: 5 blocos seguidos do mesmo minerador => 3 minutos sem minerar
- Ataque 51% pode ser disparado pelo botao no monitor

### Encerrar
```bash
docker compose down
```

## Servicos que sobem
- zookeeper
- kafka
- servidor
- minerador-1
- minerador-2
- minerador-3
- minerador-4
- minerador-5
- minerador-6
- monitor

## Observacao
Este projeto esta configurado para executar via Docker Compose.

No monitor, use o painel de simulacao de ataque para testar dominancia de hashrate e a punicao em tempo real.

Se quiser reiniciar do zero, execute:
```bash
docker compose down -v
docker compose up --build
```
