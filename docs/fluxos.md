---
title: Fluxos de Negócio
tags:
  - docs
  - fluxos
  - processos
---

# Fluxos de Negócio

[[index|← Início]] · [[permissoes|Permissões]]

## 1. Login e Navegação

```mermaid
flowchart TD
    Start([Acesso ao sistema]) --> Login["/login/\nFormulário de e-mail e senha"]
    Login --> AuthAPI["POST /api/v1/auth/login/"]
    AuthAPI --> Valid{Credenciais válidas?}
    Valid -- Não --> Erro["Exibe mensagem de erro\nno formulário"]
    Erro --> Login
    Valid -- Sim --> SetCookie["Set-Cookie: sessionid + csrftoken"]
    SetCookie --> Perfil{Qual perfil?}
    Perfil -- "admin / manager / analyst / assistant" --> Dashboard["/dashboard/\nDashboard individual"]
    Perfil -- "client" --> Portal["/portal/\nPortal do cliente"]
```

---

## 2. Ciclo de Vida de uma Tarefa

```mermaid
stateDiagram-v2
    [*] --> pending : Criar tarefa
    pending --> progress : Iniciar (btn ou PATCH status)
    progress --> done : Concluir (valida dependências)
    done --> pending : Reabrir
    pending --> late : Prazo venceu (automático)
    late --> progress : Iniciar
    progress --> late : Prazo venceu enquanto em andamento
    done --> [*] : Tarefa concluída definitivamente
    
    note right of done
        Se recorrência != none:
        sistema gera automaticamente
        próxima ocorrência
    end note
```

---

## 3. Criação e Atribuição de Tarefa

```mermaid
sequenceDiagram
    actor G as Gestor
    participant UI as Interface
    participant API as /api/v1/tarefas/
    participant DB as Banco de Dados
    participant N as Notificações

    G->>UI: Clica em "Nova Tarefa"
    UI->>UI: Abre modal com formulário
    G->>UI: Preenche título, empresa, responsável, prazo, prioridade
    UI->>API: POST /api/v1/tarefas/
    API->>API: Valida campos obrigatórios
    API->>API: Calcula prazo se tipo_prazo=days
    API->>DB: INSERT tarefa
    API->>DB: INSERT historico (acao='criou')
    API->>N: Cria notificação para o responsável (tarefa_criada)
    API-->>UI: 201 Created + objeto tarefa
    UI->>UI: Redireciona para /tarefas/{id}/
```

---

## 4. Fluxo do Timer de Trabalho

```mermaid
sequenceDiagram
    actor U as Colaborador
    participant UI as Detalhe da Tarefa
    participant API as /api/v1/tarefas/{id}/timer/

    U->>UI: Clica em "Iniciar"
    UI->>API: POST /iniciar/
    API->>API: Cria SessaoTarefa (status=ativa, inicio=now())
    API-->>UI: { id, status: 'ativa', inicio }
    UI->>UI: Inicia contador visual (setInterval)

    opt Pausar
        U->>UI: Clica em "Pausar"
        UI->>API: POST /{sessao_id}/pausar/
        API->>API: Cria PausaSessao (inicio_pausa=now())
        API->>API: Atualiza SessaoTarefa.status = 'pausada'
        UI->>UI: Para contador
    end

    opt Retomar
        U->>UI: Clica em "Retomar"
        UI->>API: POST /{sessao_id}/retomar/
        API->>API: Fecha PausaSessao (fim_pausa=now())
        API->>API: Atualiza SessaoTarefa.status = 'ativa'
        UI->>UI: Reinicia contador
    end

    U->>UI: Clica em "Finalizar"
    UI->>API: POST /{sessao_id}/finalizar/
    API->>API: SessaoTarefa.fim = now()
    API->>API: Calcula duração = (fim-inicio) - Σ pausas
    API->>API: Tarefa.tempo_total_minutos += duração
    API->>API: INSERT historico (acao='timer')
    API-->>UI: { duracao_minutos: 62 }
    UI->>UI: Exibe toast "62 minutos registrados"
```

---

## 5. Conclusão com Recorrência

```mermaid
flowchart TD
    Concluir["POST /tarefas/{id}/concluir/"] --> VerifDep{Há dependências\npendentes?}
    VerifDep -- Sim --> Erro400["400 Bad Request\nLista as dependências bloqueantes"]
    VerifDep -- Não --> AtualizaStatus["status = 'done'\nconcluida_em = now()"]
    AtualizaStatus --> RegHistorico["HistoricoTarefa\nacao='concluiu'"]
    RegHistorico --> VerifRec{recorrencia\n!= 'none'?}
    VerifRec -- Não --> Fim([Fim])
    VerifRec -- Sim --> CalcPrazo["Calcula próximo prazo\nproximo_prazo(tipo, recorrencia)"]
    CalcPrazo --> CriaNova["Cria nova Tarefa\ncom mesmos dados\nestatus='pending'"]
    CriaNova --> RegHistNova["HistoricoTarefa\nnova tarefa: acao='criou'"]
    RegHistNova --> Fim
```

---

## 6. Alertas Automáticos (Cron)

```mermaid
flowchart TD
    Cron8h["⏰ 08:00 diário\nenviar_alertas_prazo"] --> BuscaTarefas["Busca tarefas com\nprazo = amanhã\nstatus != 'done'"]
    BuscaTarefas --> ParaCadaTarefa{Para cada tarefa}
    ParaCadaTarefa --> VerifDup{"Alerta já enviado\nhoje?"}
    VerifDup -- Sim --> Skip[Pula]
    VerifDup -- Não --> CriaNotif["Cria Notificacao\ntipo='tarefa_vencendo'"]
    CriaNotif --> EnviaEmail{Email\nconfigurado?}
    EnviaEmail -- Sim --> SendEmail["Envia e-mail\npara o responsável"]
    EnviaEmail -- Não --> MarcarEnviado
    SendEmail --> MarcarEnviado["Registra em HistoricoTarefa\npara anti-duplicata"]
    
    Cron8hSeg["⏰ 08:00 segunda-feira\nenviar_relatorio_semanal"] --> GeraRelatorio["Compila métricas\nda semana anterior"]
    GeraRelatorio --> EnviaGestores["Envia e-mail\npara gestores"]
```

---

## 7. Portal do Cliente — Solicitação de Boleto

```mermaid
sequenceDiagram
    actor C as Cliente
    participant Portal as Portal (/portal/)
    participant API as /api/v1/portal/boletos/
    actor G as Gestor

    C->>Portal: Acessa /portal/boletos/
    Portal->>API: GET /boletos/
    API-->>Portal: Lista solicitações anteriores
    C->>Portal: Clica "Solicitar Boleto"
    C->>Portal: Seleciona pagamento de referência
    Portal->>API: POST /boletos/ { pagamento, observacoes }
    API->>API: Vincula à empresa do usuário logado
    API->>API: SolicitacaoBoleto.status = 'pendente'
    API-->>Portal: 201 Created
    Portal->>Portal: Exibe toast de confirmação

    Note over G: Gestor acessa a lista de solicitações
    G->>API: PATCH /boletos/{id}/ { status: 'processado' }
    API-->>G: 200 OK
```

---

## 8. Fluxo de Notificações

```mermaid
flowchart LR
    Acao["Ação no sistema\n(comentário, atribuição,\nconclusão, prazo)"]
    Acao --> CriaNotif["Cria Notificacao\nno banco"]
    CriaNotif --> BadgeSino["Badge vermelho\nno sino do header"]
    BadgeSino --> PainelAberto{Usuário abre\npainel?}
    PainelAberto -- Sim --> ListaNotif["GET /notificacoes/\nLista com mais recentes primeiro"]
    ListaNotif --> CliqueItem{Clica em\nnotificação?}
    CliqueItem -- Sim --> MarcarLida["PATCH /notificacoes/{id}/lida/"]
    MarcarLida --> NavegaTarefa["Navega para a tarefa relacionada"]
    PainelAberto -- Não --> Persiste["Notificação persiste\naté ser lida"]
```

---

Próximo: [[deploy]]
