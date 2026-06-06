# SN Gestor de Tarefas

Sistema de gestão BPO desenvolvido para a **SN Gestão Estratégica em Saúde**, com controle de tarefas, empresas clientes, dashboards de produtividade e portal do cliente.

---

## 🚀 Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Backend | Django 4.2 + Django REST Framework |
| Banco de dados | PostgreSQL 15 |
| Frontend | HTML / CSS / JavaScript (sem framework) |
| Containerização | Docker + Docker Compose |
| Proxy reverso | Nginx |

---

## 📦 Módulos

- **Autenticação** — Login com e-mail, perfis de acesso (Admin, Gestor, Analista, Assistente, Cliente)
- **Gestão de Tarefas** — CRUD completo, checklist, chat por tarefa, timer, histórico de alterações, link de documento, recorrência com geração antecipada por data final
- **Gestão de Empresas** — Cadastro, múltiplos colaboradores por empresa, histórico de pagamentos
- **Controle de Acesso por Empresa** — Analistas e assistentes visualizam apenas as empresas, tarefas e vencimentos das empresas às quais foram designados
- **Integração ContaAzul** — OAuth 2.0, sincronização de contas a pagar/receber, validação de CNPJ no vínculo, criação automática de tarefas para vencimentos
- **Dashboards** — Individual (por colaborador) e Geral (visão da operação), metas mensais
- **Colaboradores** — Desempenho da equipe com progresso de metas
- **Notificações** — Alertas de prazo por e-mail, relatório semanal automático (toda segunda-feira)
- **Relatórios PDF** — Por período, empresa ou colaborador
- **Quadro de Post-its** — Anotações rápidas pessoais e da equipe
- **Portal do Cliente** — Acesso exclusivo com documentos (Drive), histórico financeiro e solicitação de boleto
- **Gestão de Usuários** — CRUD com ativação/desativação

---

## 🗂️ Estrutura do Projeto

```
sn-gestor/
├── backend/
│   ├── apps/
│   │   ├── accounts/       # Autenticação e usuários
│   │   ├── companies/      # Empresas, pagamentos e colaboradores
│   │   ├── tasks/          # Tarefas, checklist, chat, timer, recorrência
│   │   ├── contaazul/      # Integração OAuth + sync ContaAzul
│   │   ├── dashboard/      # Dashboards e metas mensais
│   │   ├── postits/        # Quadro de post-its
│   │   ├── relatorios/     # Geração de PDF
│   │   ├── portal/         # Portal do cliente
│   │   └── frontend/       # Views HTML (serve as páginas)
│   ├── config/
│   │   └── settings/
│   │       ├── base.py       # Configurações compartilhadas
│   │       ├── development.py
│   │       ├── staging.py    # AWS sem HTTPS (sem SECURE_SSL_REDIRECT)
│   │       └── production.py
│   ├── static/             # CSS e JS globais
│   └── templates/          # Templates HTML
├── nginx/
│   └── nginx.conf          # HTTPS app.gestaomedhospitalar.com
├── docker-compose.yml
└── .env.example
```

---

## ⚙️ Como rodar localmente

### Pré-requisitos
- [Docker](https://www.docker.com/) instalado
- [Docker Compose](https://docs.docker.com/compose/) instalado

### Passos

**1. Clone o repositório**
```bash
git clone https://github.com/nuanderson/sn-gestor-tarefas.git
cd sn-gestor-tarefas
```

**2. Configure as variáveis de ambiente**
```bash
cp .env.example .env
# Edite o .env com suas credenciais
```

**3. Suba os containers**
```bash
docker compose up -d
```

**4. Crie o superusuário**
```bash
docker compose exec backend python manage.py createsuperuser
```

**5. Acesse o sistema**
- Sistema: http://localhost
- Admin Django: http://localhost/admin

---

## 🔑 Perfis de Acesso

| Perfil | Acesso |
|--------|--------|
| `admin` | Acesso total ao sistema |
| `manager` | Gestor — cria tarefas, vê todos os dashboards |
| `analyst` | Analista — executa suas tarefas |
| `assistant` | Assistente — executa suas tarefas |
| `client` | Cliente — acessa apenas o Portal do Cliente |

---

## 🌐 Rotas Principais

| URL | Descrição |
|-----|-----------|
| `/login/` | Página de login |
| `/dashboard/` | Dashboard individual |
| `/dashboard/geral/` | Visão geral da operação (gestor) |
| `/dashboard/colaboradores/` | Desempenho da equipe (gestor) |
| `/tarefas/` | Lista de tarefas |
| `/empresas/` | Lista de empresas |
| `/financeiro/` | Vencimentos ContaAzul (todos os perfis) |
| `/postits/` | Quadro de post-its |
| `/relatorios/` | Relatórios PDF |
| `/usuarios/` | Gestão de usuários (admin) |
| `/perfil/` | Perfil do usuário logado |
| `/portal/` | Portal do cliente |
| `/contaazul/connect/<id>/` | Inicia OAuth ContaAzul |
| `/contaazul/callback/` | Callback OAuth ContaAzul |
| `/api/v1/` | API REST |

---

## 🗃️ Variáveis de Ambiente

```env
SECRET_KEY=sua-chave-secreta
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.staging

ALLOWED_HOSTS=app.gestaomedhospitalar.com

POSTGRES_DB=sn_gestor_db
POSTGRES_USER=sn_gestor_user
POSTGRES_PASSWORD=sua-senha
POSTGRES_HOST=db
POSTGRES_PORT=5432

TIME_ZONE=America/Sao_Paulo

# E-mail SMTP
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seuemail@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app

# ContaAzul OAuth 2.0
CONTAAZUL_CLIENT_ID=seu_client_id
CONTAAZUL_CLIENT_SECRET=seu_client_secret
CONTAAZUL_REDIRECT_URI=https://app.gestaomedhospitalar.com/contaazul/callback/
```

---

## 📋 Fases de Desenvolvimento

- [x] Fase 1 — Projeto Django estruturado, Docker Compose, banco rodando
- [x] Fase 2 — Autenticação, perfis de acesso, login/logout
- [x] Fase 3 — Empresas, usuários, tarefas (CRUD completo)
- [x] Fase 4 — Checklist, chat por tarefa, histórico, links de documentos
- [x] Fase 5 — Dashboards, metas mensais, relatórios PDF
- [x] Fase 6 — Notificações, e-mails automáticos
- [x] Fase 7 — Quadro de post-its
- [x] Fase 8 — Frontend completo (todas as telas)
- [x] Fase 9 — Portal do cliente
- [x] Fase 10 — Integração ContaAzul (OAuth 2.0, sync vencimentos, validação CNPJ)
- [x] Fase 11 — Controle de acesso por empresa (colaboradores por empresa, filtros por perfil)
- [x] Fase 12 — Recorrência com data final (geração antecipada de todas as ocorrências)
- [x] Deploy — AWS EC2 · `app.gestaomedhospitalar.com` · HTTPS (Let's Encrypt) · Docker

---

## 👩‍💼 Sobre

Desenvolvido para a **SN Gestão Estratégica em Saúde**.  
Sistema de uso interno para gestão de equipe, clientes e tarefas BPO.
