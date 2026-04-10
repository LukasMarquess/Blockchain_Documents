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
- monitor

## Observacao
Este projeto esta configurado para executar via Docker Compose.

Se quiser reiniciar do zero, execute:
```bash
docker compose down -v
docker compose up --build
```
