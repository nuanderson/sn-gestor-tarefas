---
title: Referência da API
tags:
  - docs
  - api
  - rest
---

# Referência da API REST

[[index|← Início]] · [[modelos-de-dados|Modelos]]

Base URL: `/api/v1/`  
Formato: JSON  
Autenticação: Sessão Django (`sessionid` cookie)  
CSRF: Header `X-CSRFToken` obrigatório em POST/PATCH/PUT/DELETE

> [!note] Paginação
> Respostas de lista retornam `{ count, next, previous, results[] }`. Tamanho padrão de página: **20 itens**.

---

## Autenticação

### `POST /api/v1/auth/login/`

Autentica o usuário e inicia sessão.

**Permissão:** AllowAny  
**Body:**
```json
{ "email": "usuario@email.com", "senha": "minhasenha" }
```
**Resposta 200:**
```json
{
  "id": 1,
  "email": "usuario@email.com",
  "nome": "João Silva",
  "perfil": "manager",
  "iniciais": "JS"
}
```
**Erros:** `400` credenciais inválidas · `400` campos obrigatórios

---

### `POST /api/v1/auth/logout/`

Encerra a sessão atual.

**Permissão:** IsAuthenticated  
**Resposta:** `200 OK`

---

### `GET /api/v1/auth/me/`

Retorna dados do usuário logado.

**Permissão:** IsAuthenticated

---

### `PATCH /api/v1/auth/me/`

Atualiza perfil do próprio usuário (nome, foto).

---

### `POST /api/v1/auth/senha/`

Altera a senha do usuário logado.

**Body:** `{ "senha_atual": "...", "nova_senha": "..." }`

---

## Tarefas

### `GET /api/v1/tarefas/`

Lista tarefas com filtros.

**Permissão:** IsEquipeInterna  
**Query params:**

| Parâmetro | Tipo | Exemplo |
|-----------|------|---------|
| `empresa` | int | `?empresa=5` |
| `responsavel` | int | `?responsavel=3` |
| `status` | string | `?status=pending` |
| `prioridade` | string | `?prioridade=urgent` |
| `categoria` | string | `?categoria=fiscal` |
| `tag` | int | `?tag=2` |
| `busca` | string | `?busca=declaração` |
| `prazo_de` | date | `?prazo_de=2025-01-01` |
| `prazo_ate` | date | `?prazo_ate=2025-01-31` |

---

### `POST /api/v1/tarefas/`

Cria nova tarefa. Registra `HistoricoTarefa` com ação `criou` automaticamente.

**Permissão:** IsEquipeInterna  
**Body:**
```json
{
  "titulo": "Entregar SPED Fiscal",
  "empresa": 3,
  "responsavel": 7,
  "prazo": "2025-02-28",
  "prioridade": "high",
  "categoria": "fiscal",
  "recorrencia": "monthly",
  "observacoes": "Referente ao mês de janeiro.",
  "link_documento": "https://drive.google.com/..."
}
```
**Resposta:** `201 Created` com objeto `Tarefa` completo

---

### `GET /api/v1/tarefas/{id}/`

Retorna tarefa com todos os detalhes aninhados: checklist, comentários, histórico, dependências, sessão ativa.

**Permissão:** IsEquipeInterna

---

### `PATCH /api/v1/tarefas/{id}/`

Atualiza campos da tarefa. Gera `HistoricoTarefa` com ação `editou` listando campos alterados.

**Permissão:** IsEquipeInterna

---

### `DELETE /api/v1/tarefas/{id}/`

Remove a tarefa permanentemente.

**Permissão:** IsGestorOuAcima

---

### `POST /api/v1/tarefas/{id}/concluir/`

Conclui a tarefa. Valida se todas as dependências estão concluídas. Se `recorrencia != 'none'`, cria automaticamente a próxima ocorrência.

**Permissão:** IsEquipeInterna  
**Resposta 400** se houver dependências pendentes:
```json
{ "erro": "Existem tarefas dependentes não concluídas: Tarefa X, Tarefa Y" }
```

---

### `POST /api/v1/tarefas/{id}/reabrir/`

Reabre uma tarefa concluída, voltando ao status `pending`.

---

### `GET /api/v1/tarefas/hoje/`

Retorna tarefas com prazo para hoje do usuário logado.

---

### `GET /api/v1/tarefas/atrasadas/`

Retorna tarefas com prazo vencido (excluindo concluídas).

---

## Checklist

### `GET /api/v1/tarefas/{id}/checklist/`

Lista itens do checklist da tarefa.

### `POST /api/v1/tarefas/{id}/checklist/`

Adiciona item. **Body:** `{ "titulo": "Revisar documento" }`

### `PATCH /api/v1/tarefas/{id}/checklist/{item_id}/`

Atualiza item (marcar como concluído, renomear).  
**Body:** `{ "concluido": true }`

### `DELETE /api/v1/tarefas/{id}/checklist/{item_id}/`

Remove item do checklist.

---

## Comentários

### `GET /api/v1/tarefas/{id}/comentarios/`

Lista comentários ordenados por data.

### `POST /api/v1/tarefas/{id}/comentarios/`

Adiciona comentário. Salva autor automaticamente. Gera notificação para o responsável da tarefa.

**Body:** `{ "texto": "Aguardando retorno do cliente." }`

---

## Dependências

### `GET /api/v1/tarefas/{id}/dependencias/`

Lista tarefas das quais esta depende.

### `POST /api/v1/tarefas/{id}/dependencias/`

Adiciona dependência. **Body:** `{ "depende_de": 12 }`  
**Erro 400** em dependência circular.

### `DELETE /api/v1/tarefas/{id}/dependencias/{dep_id}/`

Remove dependência.

---

## Timer

### `GET /api/v1/tarefas/{id}/timer/sessao-ativa/`

Retorna a sessão de timer ativa, se existir.

**Resposta:**
```json
{
  "id": 5,
  "status": "ativa",
  "inicio": "2025-01-15T09:30:00-03:00",
  "tempo_decorrido_segundos": 3720
}
```

### `POST /api/v1/tarefas/{id}/timer/iniciar/`

Inicia nova sessão de timer. Apenas uma sessão ativa por tarefa/usuário.

### `POST /api/v1/tarefas/{id}/timer/{sessao_id}/pausar/`

Pausa a sessão, registrando início da pausa.

### `POST /api/v1/tarefas/{id}/timer/{sessao_id}/retomar/`

Retoma sessão pausada, fechando o registro de pausa.

### `POST /api/v1/tarefas/{id}/timer/{sessao_id}/finalizar/`

Finaliza sessão, calcula duração líquida e acumula em `Tarefa.tempo_total_minutos`.

**Resposta:**
```json
{ "duracao_minutos": 62 }
```

---

## Notificações

### `GET /api/v1/notificacoes/`

Lista notificações do usuário logado. Não lidas aparecem primeiro.

### `POST /api/v1/notificacoes/todas-lidas/`

Marca todas as notificações como lidas.

### `PATCH /api/v1/notificacoes/{id}/lida/`

Marca notificação específica como lida.

---

## Usuários

**Base:** `/api/v1/usuarios/`  
**Permissão:** IsAdministrador (exceto onde indicado)

### `GET /api/v1/usuarios/`

Lista usuários com filtros: `?perfil=manager`, `?ativo=true`, `?busca=joão`

### `GET /api/v1/usuarios/equipe/`

Lista apenas equipe interna (exclui clientes). **Permissão:** IsEquipeInterna

### `POST /api/v1/usuarios/`

Cria usuário. A senha inicial pode ser enviada no body.

### `DELETE /api/v1/usuarios/{id}/`

**Soft delete** — define `is_active = False`. Dados preservados.

### `GET /api/v1/usuarios/{usuario_id}/produtividade/`

Métricas de produtividade. **Query params:** `?periodo=mes|semana|hoje`

**Resposta:**
```json
{
  "tarefas_concluidas": 12,
  "horas_registradas": 45.5,
  "tarefas_em_aberto": 3,
  "tarefas_atrasadas": 1
}
```

---

## Empresas

**Base:** `/api/v1/empresas/`

### `GET /api/v1/empresas/`

**Permissão:** IsEquipeInterna  
**Filtros:** `?status=ativo`, `?busca=nome`

### `GET /api/v1/empresas/resumo/`

Resumo financeiro: total de empresas, faturamento mensal, inadimplências.

### `GET /api/v1/empresas/{id}/pagamentos/`

Lista pagamentos da empresa.

### `POST /api/v1/empresas/{id}/pagamentos/`

Registra pagamento. **Body:**
```json
{
  "referencia": "2025-01",
  "valor": 1500.00,
  "status": "pago",
  "pago_em": "2025-01-10"
}
```

---

## Dashboard

**Permissão base:** IsGestorOuAcima (exceto individual)

### `GET /api/v1/dashboard/geral/?mes=1&ano=2025`

Painel consolidado da operação. Retorna:
- `resumo`: total de tarefas, concluídas no mês, atrasadas, horas
- `por_categoria`: contagem por categoria
- `por_empresa`: top 10 empresas por volume de tarefas
- `tempo_por_colaborador`: horas por colaborador no período

### `GET /api/v1/dashboard/individual/?mes=1&ano=2025`

Dashboard pessoal. Gestores podem consultar outros usuários com `?usuario_id=5`.  
Retorna: métricas, meta do mês, próximas tarefas, últimas concluídas.

### `GET /api/v1/dashboard/colaboradores/?mes=1&ano=2025`

Resumo de todos os colaboradores ativos com progresso de metas.

### CRUD `/api/v1/dashboard/metas/`

Gerencia metas mensais por colaborador (GET, POST, PATCH, DELETE).

---

## Portal do Cliente

**Permissão:** IsCliente (usuários com `perfil = 'client'`)

### `GET /api/v1/portal/resumo/`

Painel inicial do cliente: dados da empresa, saldo em aberto, documentos recentes.

### `GET /api/v1/portal/documentos/`

Documentos compartilhados com a empresa do cliente (links Google Drive).

### `GET /api/v1/portal/pagamentos/`

Histórico de pagamentos da empresa.

### `POST /api/v1/portal/boletos/`

Solicita geração de boleto para um pagamento. **Body:** `{ "pagamento": 5, "observacoes": "..." }`

---

## Post-its

**Base:** `/api/v1/postits/`  
**Permissão:** IsEquipeInterna

### `GET /api/v1/postits/`

Retorna dois grupos: `meus` (privados do usuário) e `equipe` (visíveis para todos).

### `POST /api/v1/postits/`

**Body:**
```json
{
  "titulo": "Lembrete",
  "texto": "Enviar relatório até sexta.",
  "cor": "amarelo",
  "visibilidade": "equipe"
}
```

### `PATCH /api/v1/postits/{id}/fixar/`

Alterna o estado de fixado/desfixado.

---

## Relatórios PDF

**Permissão:** IsGestorOuAcima

### `GET /api/v1/relatorios/tarefas/pdf/`

Gera PDF com lista de tarefas filtradas.

**Query params:** `data_inicio`, `data_fim`, `empresa_id`, `colaborador_id`, `status`  
**Resposta:** `Content-Type: application/pdf` (download)

### `GET /api/v1/relatorios/colaborador/pdf/`

Gera PDF de produtividade mensal por colaborador.

**Query params:** `mes`, `ano`, `colaborador_id`

---

## Tags

**Base:** `/api/v1/tags/`

| Método | Permissão |
|--------|-----------|
| GET (list/retrieve) | IsEquipeInterna |
| POST / PUT / DELETE | IsGestorOuAcima |

---

Próximo: [[permissoes]]
