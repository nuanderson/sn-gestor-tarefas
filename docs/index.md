---
title: SN Gestor — Documentação Técnica
tags:
  - docs
  - index
aliases:
  - Home
  - Início
---

# SN Gestor — Documentação Técnica

Sistema de gestão de tarefas BPO desenvolvido para a **Suzane Neves Gestão Estratégica em Saúde**.

> [!info] Versão
> SN Gestor v3.0 · Django 4.2 · PostgreSQL 15 · Docker · AWS EC2 · HTTPS

## Navegação

| Documento | Descrição |
|-----------|-----------|
| [[arquitetura]] | Visão geral do sistema, stack e estrutura de pastas |
| [[modelos-de-dados]] | Entidades, campos e relacionamentos (diagrama ER) |
| [[api-referencia]] | Todos os endpoints REST com métodos e permissões |
| [[permissoes]] | Perfis de usuário e matriz de controle de acesso |
| [[fluxos]] | Fluxos de negócio com diagramas (tarefas, timer, portal, ContaAzul) |
| [[deploy]] | Infraestrutura Docker, AWS, HTTPS e variáveis de ambiente |
| [[modulos]] | Detalhamento de cada app Django incluindo ContaAzul |

## Visão Geral Rápida

```
Usuário → Nginx (80) → Django (8000) → PostgreSQL (5432)
                    ↘ Static/Media files
Scheduler → Cron → Django management commands
```

**Módulos principais:**

- `accounts` — Autenticação e usuários (5 perfis)
- `tasks` — Tarefas, checklist, comentários, timer, histórico, recorrência com data final
- `companies` — Empresas clientes, pagamentos e colaboradores por empresa
- `contaazul` — Integração OAuth 2.0 com ContaAzul, sync de vencimentos
- `dashboard` — Painéis gerenciais e metas mensais
- `portal` — Portal exclusivo para clientes
- `postits` — Quadro de recados interno
- `relatorios` — Geração de PDF com WeasyPrint

## Links Rápidos

- [[api-referencia#Autenticação|Login / Logout]]
- [[api-referencia#Tarefas|Endpoints de Tarefas]]
- [[api-referencia#Timer|Timer de Trabalho]]
- [[deploy#Variáveis de Ambiente|Configurar .env]]
- [[permissoes#Matriz de Acesso|Matriz de Permissões]]
