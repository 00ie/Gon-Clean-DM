# Gon Clean DM

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-red.svg)
![Release](https://img.shields.io/badge/Release-1.0.1-brightgreen.svg)
![UI](https://img.shields.io/badge/UI-CustomTkinter-2ea44f.svg)

## Features

- Backup em TXT e CSV
- Limpeza em massa com filtros por data, conteudo e tipo
- Selecionar varios canais de uma vez
- Busca de mensagens por termo
- Interface escura com status em tempo real
- Lista de chats com filtro e IDs opcionais
- Avatares com cache local

## Instalacao

### Requisitos

- Python 3.8 ou superior
- pip

### Setup

```bash
git clone https://github.com/00ie/gon-clean-dm.git
cd gon-clean-dm
pip install -r requirements.txt
python main.py
```

## Uso

1. Abra o aplicativo e insira o token do Discord
2. Selecione um ou mais chats
3. Escolha entre backup ou limpeza

### Backup

```text
Selecione os canais -> Escolha TXT ou CSV -> Exporte
```

### Limpeza

```text
Defina filtros -> Confirme a delecao
```

## Estrutura do Projeto

```
gon-clean-dm/
├── main.py
├── requirements.txt
├── README.md
├── assets/
├── src/
│   ├── core/
│   └── ui/
├── exports/
├── logs/
└── .cache/
```

## Configuracao

O token nao e salvo no pc, ele fica apenas em memoria durante a execucao.

## Avisos Legais

- Use este software de forma responsavel
- Respeite os Termos de Servico do Discord
- Nao compartilhe seu token

## Licenca

MIT. Veja `LICENSE`.

## Changelog

### Version 1.0.1

- Interface mais limpa
- Lista de chats com filtro, selecao e IDs opcionais
- Avatares com cache local
- Estrutura de pastas organizada
- Exports e logs padronizados
