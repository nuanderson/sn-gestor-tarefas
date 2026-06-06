---
title: Modelos de Dados
tags:
  - docs
  - modelos
  - banco-de-dados
---

# Modelos de Dados

[[index|← Início]] · [[arquitetura|Arquitetura]]

## Diagrama ER

```mermaid
erDiagram
    Usuario {
        int id PK
        string email UK
        string nome
        string perfil
        bool is_active
        int empresa_id FK
    }
    Empresa {
        int id PK
        string nome
        string cnpj
        string status
        decimal mensalidade
        int responsavel_id FK
    }
    Tarefa {
        int id PK
        string titulo
        string status
        string prioridade
        string categoria
        string tipo_prazo
        date prazo
        string recorrencia
        int empresa_id FK
        int responsavel_id FK
        int criado_por_id FK
        datetime criado_em
        datetime concluida_em
    }
    Tag {
        int id PK
        string nome
        string cor
        int criado_por_id FK
    }
    TarefaDependencia {
        int id PK
        int tarefa_id FK
        int depende_de_id FK
    }
    ChecklistItem {
        int id PK
        int tarefa_id FK
        string titulo
        bool concluido
        datetime concluido_em
    }
    Comentario {
        int id PK
        int tarefa_id FK
        int autor_id FK
        string texto
        bool editado
        datetime criado_em
    }
    HistoricoTarefa {
        int id PK
        int tarefa_id FK
        int usuario_id FK
        string acao
        string detalhe
        datetime criado_em
    }
    SessaoTarefa {
        int id PK
        int tarefa_id FK
        int usuario_id FK
        string status
        datetime inicio
        datetime fim
        int duracao_minutos
    }
    PausaSessao {
        int id PK
        int sessao_id FK
        datetime inicio_pausa
        datetime fim_pausa
    }
    Notificacao {
        int id PK
        int usuario_id FK
        int tarefa_id FK
        string tipo
        string mensagem
        bool lida
        datetime criado_em
    }
    Pagamento {
        int id PK
        int empresa_id FK
        date referencia
        decimal valor
        string status
        date pago_em
    }
    MetaMensal {
        int id PK
        int colaborador_id FK
        int criado_por_id FK
        int mes
        int ano
        int meta_tarefas
        int meta_horas
    }
    Documento {
        int id PK
        int empresa_id FK
        int criado_por_id FK
        string titulo
        string tipo
        string link_drive
        datetime criado_em
    }
    SolicitacaoBoleto {
        int id PK
        int empresa_id FK
        int pagamento_id FK
        int solicitado_por_id FK
        string status
        string observacoes
        datetime criado_em
    }
    PostIt {
        int id PK
        int autor_id FK
        string titulo
        string texto
        string cor
        string visibilidade
        bool fixado
        datetime criado_em
    }

    Usuario }o--|| Empresa : "pertence a (cliente)"
    Empresa ||--o{ Tarefa : "tem"
    Usuario ||--o{ Tarefa : "é responsável"
    Usuario ||--o{ Tarefa : "criou"
    Tarefa }o--o{ Tag : "tagged with"
    Tarefa ||--o{ TarefaDependencia : "depende de"
    Tarefa ||--o{ ChecklistItem : "tem"
    Tarefa ||--o{ Comentario : "tem"
    Tarefa ||--o{ HistoricoTarefa : "registra"
    Tarefa ||--o{ SessaoTarefa : "tem"
    Tarefa ||--o{ Notificacao : "gera"
    SessaoTarefa ||--o{ PausaSessao : "tem"
    Empresa ||--o{ Pagamento : "tem"
    Empresa ||--o{ Documento : "tem"
    Empresa ||--o{ SolicitacaoBoleto : "tem"
    Usuario ||--o{ MetaMensal : "tem meta"
    Usuario ||--o{ PostIt : "escreve"
```

---

## Detalhamento por Modelo

### `Usuario`

Modelo customizado que substitui o `AbstractBaseUser` do Django. Autenticação por e-mail (sem `username`).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `email` | EmailField (unique) | Identificador de login |
| `nome` | CharField | Nome completo |
| `perfil` | CharField (choices) | `admin` · `manager` · `analyst` · `assistant` · `client` |
| `empresa` | FK → Empresa (null) | Apenas para perfil `client` |
| `is_active` | bool | Soft delete — desativação em vez de exclusão |
| `foto` | ImageField (null) | Avatar (processado com Pillow) |

**Properties úteis:** `iniciais`, `primeiro_nome`, `is_admin`, `is_gestor_ou_acima`, `is_equipe_interna`, `is_cliente`

---

### `Tarefa`

Entidade central do sistema.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `status` | choices | `pending` · `progress` · `done` · `late` |
| `prioridade` | choices | `low` · `medium` · `high` · `urgent` |
| `categoria` | choices | `fiscal` · `financeiro` · `contabil` · `folha` · `juridico` · `outros` |
| `tipo_prazo` | choices | `fixed` (data fixa) · `continuous` (contínuo) · `days` (X dias úteis) |
| `recorrencia` | choices | `none` · `weekdays` · `daily` · `weekly` · `biweekly` · `monthly` · `yearly` |
| `tempo_total_minutos` | int | Acumulado de todas as sessões finalizadas |
| `link_documento` | URLField (null) | Link do Google Drive |

> [!tip] Recorrência
> Quando uma tarefa recorrente é concluída, o sistema gera automaticamente a próxima ocorrência com prazo calculado por `proximo_prazo()`. O histórico é iniciado do zero.

---

### `TarefaDependencia`

Grafo de dependências entre tarefas. Uma tarefa pode depender de várias outras e só pode ser concluída quando todas as dependências estão com `status = 'done'`.

> [!warning] Validação
> O serializer impede dependência circular (A → B → A).

---

### `SessaoTarefa` + `PausaSessao`

Sistema de time tracking com granularidade de segundos.

```mermaid
stateDiagram-v2
    [*] --> ativa : iniciar()
    ativa --> pausada : pausar()
    pausada --> ativa : retomar()
    ativa --> finalizada : finalizar()
    pausada --> finalizada : finalizar()
    finalizada --> [*]
```

A duração líquida é calculada descontando os intervalos de `PausaSessao`:

```
duracao = (fim - inicio) - Σ(fim_pausa - inicio_pausa)
```

O resultado é salvo em `duracao_minutos` (inteiro) e somado a `Tarefa.tempo_total_minutos`.

---

### `HistoricoTarefa`

Audit trail imutável. Toda mutação relevante gera um registro.

| `acao` | Quando é gerado |
|--------|----------------|
| `criou` | POST /tarefas/ |
| `editou` | PATCH /tarefas/{id}/ com campos alterados |
| `concluiu` | POST /tarefas/{id}/concluir/ |
| `reabriu` | POST /tarefas/{id}/reabrir/ |
| `comentou` | POST /tarefas/{id}/comentarios/ |
| `checklist` | PATCH /tarefas/{id}/checklist/{item_id}/ |
| `timer` | POST /tarefas/{id}/timer/finalizar/ |

---

### `Notificacao`

| `tipo` | Gatilho |
|--------|---------|
| `tarefa_vencendo` | Cron 8h — prazo amanhã |
| `tarefa_atrasada` | Cron 8h — prazo passou |
| `comentario_novo` | Novo comentário na tarefa |
| `tarefa_concluida` | Tarefa marcada como concluída |
| `tarefa_criada` | Nova tarefa atribuída ao usuário |
| `timer_lembrete` | Timer rodando por muito tempo (futuro) |

---

### `MetaMensal`

Meta de produtividade mensal por colaborador, gerenciada por gestores.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `meta_tarefas` | int | Número de tarefas a concluir no mês |
| `meta_horas` | int | Horas a registrar no mês |
| `progresso_tarefas_pct` | computed | Calculado no serializer vs métricas reais |

---

Próximo: [[api-referencia]]
