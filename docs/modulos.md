---
title: Módulos do Sistema
tags:
  - docs
  - módulos
  - django
---

# Módulos do Sistema

[[index|← Início]] · [[deploy|Deploy]]

Cada app Django tem responsabilidade única. O módulo `tasks` é o núcleo; os demais orbitam ao redor dele.

---

## `accounts` — Usuários e Autenticação

**Responsabilidade:** Gerenciamento de identidade, autenticação por e-mail e controle de perfis.

| Arquivo | Conteúdo |
|---------|----------|
| `models.py` | `Usuario` (CustomUser), `UsuarioManager` |
| `serializers.py` | `UsuarioSerializer`, `UsuarioCriarSerializer`, `MeSerializer` |
| `views.py` | `LoginAPIView`, `LogoutAPIView`, `MeAPIView`, `UsuarioViewSet` |
| `permissions.py` | `IsAdministrador`, `IsGestorOuAcima`, `IsEquipeInterna`, `IsCliente` |

**Pontos de atenção:**
- Autenticação via e-mail, sem `username`
- Soft delete: `DELETE /usuarios/{id}/` define `is_active=False`
- Fotos de perfil processadas com Pillow (redimensionamento automático)

---

## `tasks` — Motor de Tarefas

**Responsabilidade:** Núcleo do sistema. Tarefas, checklist, comentários, timer, histórico, dependências, notificações e recorrência.

| Arquivo | Conteúdo |
|---------|----------|
| `models.py` | `Tag`, `Tarefa`, `TarefaDependencia`, `ChecklistItem`, `Comentario`, `HistoricoTarefa`, `SessaoTarefa`, `PausaSessao`, `Notificacao` |
| `serializers.py` | `TarefaSerializer`, `TarefaDetalheSerializer`, `TarefaCriarSerializer` + serializers auxiliares |
| `views.py` | `TarefaViewSet`, `TimerAPIView`, `NotificacaoAPIView`, `ProdutividadeView` |
| `utils.py` | `proximo_prazo()` — calcula data da próxima ocorrência por tipo de recorrência |

**Lógicas complexas:**
- **Recorrência com data final:** ao criar com `recorrencia_fim`, o `TarefaCriarSerializer` gera todas as ocorrências de uma vez usando `proximo_prazo()` em loop. Cada ocorrência gerada recebe `recorrencia='none'` para não disparar nova geração.
- **Recorrência individual (legado):** se `recorrencia_fim` não for informado, o comportamento original persiste — ao concluir, a próxima ocorrência é criada automaticamente.
- **Filtro por empresa:** analistas e assistentes veem apenas tarefas das empresas onde são colaboradores ou responsáveis.
- **Dependências:** `concluir` valida o grafo de `TarefaDependencia` antes de permitir a conclusão.
- **Timer:** duração líquida descontando pausas; acumulada em `tempo_total_minutos`.
- **Histórico:** toda mutação relevante cria um `HistoricoTarefa` (audit trail imutável).

**Campo `recorrencia_fim`:**
```python
recorrencia_fim = models.DateField('Repetir até', null=True, blank=True)
# Se informado ao criar → gera todas as ocorrências antecipadamente
# Se nulo → comportamento padrão (uma ocorrência por vez ao concluir)
```

---

## `companies` — Empresas e Finanças

**Responsabilidade:** Cadastro de clientes BPO, rastreamento de pagamentos e controle de acesso por colaborador.

| Arquivo | Conteúdo |
|---------|----------|
| `models.py` | `Empresa`, `Pagamento` |
| `serializers.py` | `EmpresaSerializer`, `EmpresaDetalheSerializer`, `PagamentoSerializer`, `ColaboradorSimpleSerializer` |
| `views.py` | `EmpresaViewSet` com action `pagamentos` e `resumo` |

**Campos relevantes de `Empresa`:**
- `cnpj` — único, validado no vínculo com ContaAzul
- `mensalidade` — valor mensal do contrato
- `status` — `active` · `inactive`
- `responsavel` — FK para `Usuario` (gestor responsável principal)
- `colaboradores` — ManyToMany para `Usuario` (múltiplos analistas/assistentes por empresa)

**Filtro de acesso:**
Analistas e assistentes (`perfil not in ['admin', 'manager']`) recebem automaticamente apenas as empresas onde aparecem em `responsavel` ou `colaboradores`. A lógica está em `EmpresaViewSet.get_queryset()`:
```python
if not user.is_gestor_ou_acima:
    qs = qs.filter(Q(responsavel=user) | Q(colaboradores=user)).distinct()
```

---

## `contaazul` — Integração ContaAzul

**Responsabilidade:** Conexão OAuth 2.0 com o ERP ContaAzul por empresa, sincronização de contas a pagar/receber e criação automática de tarefas financeiras.

| Arquivo | Conteúdo |
|---------|----------|
| `models.py` | `ContaAzulToken`, `ContaAzulVencimento` |
| `services.py` | `ContaAzulClient` — OAuth, refresh de token, sync |
| `views.py` | `oauth_connect`, `oauth_callback`, `sync_empresa`, `VencimentoListView`, `ConnectionStatusView` |
| `serializers.py` | `ContaAzulVencimentoSerializer`, `ContaAzulTokenStatusSerializer` |

**Fluxo OAuth:**
1. Gestor clica em "Conectar ContaAzul" na tela da empresa → `GET /contaazul/connect/<id>/`
2. Redireciona para `auth.contaazul.com` com `client_id`, `redirect_uri` e `state`
3. Usuário loga no ContaAzul → redirecionado para `GET /contaazul/callback/?code=...`
4. Backend troca o `code` por `access_token` + `refresh_token`
5. **Validação de CNPJ:** consulta `GET /v1/empresa` no ContaAzul e compara com o CNPJ cadastrado no SN Gestor — rejeita se divergir
6. Salva `ContaAzulToken` vinculado à empresa

**Sincronização:**
- Busca contas a pagar e receber nos últimos 30 dias e próximos 90 dias
- `update_or_create` por `contaazul_id` — nunca duplica
- Novas contas a pagar → cria `Tarefa` automática com prazo, valor e prioridade calculada
- Status `pago/cancelado` → fecha a tarefa vinculada automaticamente
- Token expirado → renovado automaticamente via `refresh_token` antes de cada chamada

**Filtro de acesso:**
Analistas e assistentes veem apenas vencimentos das suas empresas designadas (mesmo filtro de `companies`).

---

## `dashboard` — Painéis Gerenciais

**Responsabilidade:** Agregações e métricas para tomada de decisão.

| Endpoint | Dados retornados |
|----------|-----------------|
| `geral/` | Resumo operacional, tarefas por categoria, por empresa, horas por colaborador |
| `individual/` | Métricas pessoais, meta do mês, próximas tarefas, últimas concluídas |
| `colaboradores/` | Visão do time: cada colaborador com % de meta atingida |
| `metas/` | CRUD de `MetaMensal` por colaborador |

> [!note] Performance
> As views de dashboard fazem queries com `annotate`, `aggregate` e `values()` diretamente no ORM. Para operações de grande volume, considerar cache (Django cache framework ou Redis).

---

## `portal` — Portal do Cliente

**Responsabilidade:** Interface exclusiva para usuários `client`, isolada da operação interna.

| Funcionalidade | Descrição |
|----------------|-----------|
| Resumo | Saldo em aberto, último pagamento, documentos recentes |
| Documentos | Links de Google Drive compartilhados pela equipe (contratos, relatórios) |
| Pagamentos | Histórico de mensalidades (status: pago · pendente · atrasado) |
| Boletos | Solicitação de boleto vinculada a um pagamento pendente |

**Segurança:** Todos os dados são filtrados por `request.user.empresa`, impedindo acesso cross-tenant.

---

## `postits` — Quadro de Recados

**Responsabilidade:** Notas rápidas para a equipe interna.

| Campo | Opções |
|-------|--------|
| `cor` | `amarelo` · `verde` · `azul` · `rosa` · `roxo` |
| `visibilidade` | `privado` (só autor) · `equipe` (todos internos) |
| `fixado` | bool — destaca no topo do quadro |

Gestores podem moderar (excluir posts de terceiros).

---

## `relatorios` — Geração de PDF

**Responsabilidade:** Exportação de dados operacionais em PDF.

| Relatório | Filtros | Engine |
|-----------|---------|--------|
| Lista de tarefas | data_inicio/fim, empresa, colaborador, status | WeasyPrint |
| Produtividade por colaborador | mês, ano, colaborador | WeasyPrint |

**Dependências do sistema** (instaladas no Docker):
```
libpango, libcairo, libffi, fonts-liberation
```
Necessárias para o WeasyPrint renderizar HTML → PDF com suporte a fontes e layout CSS.

---

## `frontend` — Roteamento de Views HTML

**Responsabilidade:** Views Django simples que renderizam os templates HTML para cada rota.

Não contém lógica de negócio. Cada view verifica autenticação e delega toda a lógica ao JavaScript via API REST.

| URL | Template |
|-----|---------|
| `/` · `/dashboard/` | `dashboard/individual.html` |
| `/dashboard/geral/` | `dashboard/geral.html` |
| `/dashboard/colaboradores/` | `dashboard/colaboradores.html` |
| `/tarefas/` | `tarefas/lista.html` |
| `/tarefas/<id>/` | `tarefas/detalhe.html` |
| `/empresas/` | `empresas/lista.html` |
| `/empresas/<id>/` | `empresas/detalhe.html` |
| `/postits/` | `postits/quadro.html` |
| `/relatorios/` | `relatorios/index.html` |
| `/usuarios/` | `usuarios/lista.html` |
| `/perfil/` | `usuarios/perfil.html` |
| `/portal/` | `portal/dashboard.html` |

---

## JavaScript Principal (`static/js/api.js`)

Wrapper global para todas as chamadas à API REST. Usado em todos os templates.

```javascript
// Uso padrão
const dados = await api.get('/api/v1/tarefas/', { status: 'pending' });
const nova  = await api.post('/api/v1/tarefas/', { titulo: '...', empresa: 3 });
await api.patch('/api/v1/tarefas/5/', { status: 'done' });
await api.delete('/api/v1/tarefas/5/');
```

**Funcionalidades do `api.js`:**
- Injeta `X-CSRFToken` automaticamente em todas as requisições de escrita
- Serializa query params em GET
- Lança `Error` com a mensagem do servidor em erros HTTP
- Funções utilitárias: `toast()`, `badgeStatus()`, `formatarData()`, `tempoRelativo()`, `initiais()`, `modalAbrir()`, `modalFechar()`

---

[[index|← Voltar ao índice]]
