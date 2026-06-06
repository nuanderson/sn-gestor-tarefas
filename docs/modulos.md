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
- **Recorrência:** ao concluir, `proximo_prazo()` calcula a data da próxima tarefa e ela é criada automaticamente com os mesmos metadados
- **Dependências:** `concluir` valida o grafo de `TarefaDependencia` antes de permitir a conclusão
- **Timer:** duração líquida descontando pausas; acumulada em `tempo_total_minutos`
- **Histórico:** toda mutação relevante cria um `HistoricoTarefa` (audit trail imutável)

---

## `companies` — Empresas e Finanças

**Responsabilidade:** Cadastro de clientes BPO e rastreamento de pagamentos.

| Arquivo | Conteúdo |
|---------|----------|
| `models.py` | `Empresa`, `Pagamento` |
| `serializers.py` | `EmpresaSerializer`, `EmpresaDetalheSerializer`, `PagamentoSerializer` |
| `views.py` | `EmpresaViewSet` com action `pagamentos` e `resumo` |

**Campos relevantes de `Empresa`:**
- `cnpj` — validação de formato
- `mensalidade` — valor mensal do contrato
- `status` — `ativo` · `inativo` · `prospecto`
- `responsavel` — FK para `Usuario` (gestor responsável)

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
