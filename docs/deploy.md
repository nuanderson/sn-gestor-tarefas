---
title: Deploy e Infraestrutura
tags:
  - docs
  - deploy
  - docker
  - infraestrutura
---

# Deploy e Infraestrutura

[[index|← Início]] · [[fluxos|Fluxos]]

## Pré-requisitos

- Docker Desktop ≥ 24
- Docker Compose v2
- 2 GB RAM disponível
- Porta 80 livre no host

---

## Quick Start (Desenvolvimento)

```bash
# 1. Clonar o projeto e entrar na pasta
cd sn-gestor

# 2. Copiar e configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas credenciais (ver seção abaixo)

# 3. Subir todos os containers
docker compose up -d

# 4. Criar superusuário admin
docker compose exec backend python manage.py createsuperuser

# 5. Acessar o sistema
# http://localhost
```

---

## Variáveis de Ambiente

Arquivo: `sn-gestor/.env`

| Variável | Exemplo | Descrição |
|----------|---------|-----------|
| `SECRET_KEY` | `django-insecure-xxxxx` | Chave secreta Django. **Gerar uma nova em produção.** |
| `DEBUG` | `True` | `False` em produção |
| `ALLOWED_HOSTS` | `localhost,192.168.2.139` | Hosts permitidos separados por vírgula |
| `DB_NAME` | `sn_gestor` | Nome do banco PostgreSQL |
| `DB_USER` | `postgres` | Usuário do banco |
| `DB_PASSWORD` | `postgres` | Senha do banco |
| `DB_HOST` | `db` | Nome do container do banco |
| `DB_PORT` | `5432` | Porta do banco |
| `EMAIL_HOST` | `smtp.gmail.com` | Servidor SMTP |
| `EMAIL_PORT` | `587` | Porta SMTP (TLS) |
| `EMAIL_HOST_USER` | `seu@gmail.com` | E-mail remetente |
| `EMAIL_HOST_PASSWORD` | `app-password` | Senha de app do Gmail |
| `DEFAULT_FROM_EMAIL` | `SN Gestor <seu@gmail.com>` | Nome exibido no remetente |
| `TIME_ZONE` | `America/Sao_Paulo` | Fuso horário do sistema |

> [!tip] Gmail — Senha de App
> Acesse myaccount.google.com → Segurança → Senhas de app. Gere uma senha específica para o SN Gestor.

> [!warning] SECRET_KEY em Produção
> Nunca use a chave padrão. Gere uma nova com:
> ```bash
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

---

## Containers

### `db` — PostgreSQL 15

```yaml
image: postgres:15-alpine
volumes:
  - postgres_data:/var/lib/postgresql/data
healthcheck:
  test: pg_isready -U postgres
  interval: 5s
  retries: 10
```

Dados persistidos no volume `postgres_data`. O `backend` aguarda o healthcheck antes de inicializar.

---

### `backend` — Django

```yaml
build: ./backend
command: ["/app/entrypoint.sh"]
volumes:
  - ./backend:/app          # hot-reload em dev
  - static_volume:/app/staticfiles
  - media_volume:/app/media
depends_on:
  db: { condition: service_healthy }
```

**`entrypoint.sh`** (sequência de inicialização):
1. Aguarda PostgreSQL (`nc -z db 5432`)
2. `python manage.py migrate --noinput`
3. `python manage.py collectstatic --noinput --clear`
4. `python manage.py runserver 0.0.0.0:8000`

> [!warning] Produção
> Substituir o passo 4 por Gunicorn:
> ```bash
> gunicorn config.wsgi:application \
>   --bind 0.0.0.0:8000 \
>   --workers 4 \
>   --timeout 120
> ```

---

### `scheduler` — Cron Jobs

```yaml
build: ./backend
command: crond -f -l 2
```

Executa os management commands agendados via `crontab`:

```cron
0 8 * * * python manage.py enviar_alertas_prazo
0 8 * * 1 python manage.py enviar_relatorio_semanal
```

Logs gravados em `/var/log/cron.log` dentro do container.

---

### `nginx` — Proxy Reverso

```nginx
upstream django {
    server backend:8000;
}

server {
    listen 80;
    client_max_body_size 20M;

    location /static/ {
        alias /app/staticfiles/;
    }

    location /media/ {
        alias /app/media/;
    }

    location / {
        proxy_pass http://django;
    }
}
```

Arquivos estáticos e de mídia são servidos diretamente pelo Nginx (sem passar pelo Django), reduzindo carga.

---

## Volumes Docker

| Volume | Conteúdo | Consumido por |
|--------|----------|---------------|
| `postgres_data` | Dados do banco | `db` |
| `static_volume` | CSS, JS, imagens coletados | `backend`, `nginx` |
| `media_volume` | Uploads de usuários (fotos) | `backend`, `nginx` |

> [!danger] Backup
> O volume `postgres_data` contém todos os dados do sistema. Configure backups regulares com `pg_dump`.

---

## Comandos Úteis

```bash
# Ver logs em tempo real
docker compose logs -f backend

# Acessar shell do Django
docker compose exec backend python manage.py shell

# Rodar migrations manualmente
docker compose exec backend python manage.py migrate

# Criar usuário admin
docker compose exec backend python manage.py createsuperuser

# Backup do banco
docker compose exec db pg_dump -U postgres sn_gestor > backup.sql

# Restaurar backup
docker compose exec -T db psql -U postgres sn_gestor < backup.sql

# Parar tudo
docker compose down

# Parar e remover volumes (CUIDADO — apaga dados)
docker compose down -v

# Rebuild após mudanças no Dockerfile
docker compose up -d --build
```

---

## Checklist de Deploy em Produção

- [ ] Gerar novo `SECRET_KEY` no `.env`
- [ ] Definir `DEBUG=False`
- [ ] Configurar `ALLOWED_HOSTS` com o domínio real
- [ ] Substituir `runserver` por Gunicorn no `entrypoint.sh`
- [ ] Configurar HTTPS no Nginx (Let's Encrypt / Certbot)
- [ ] Remover IPs hardcoded do `nginx.conf` (`server_name`)
- [ ] Configurar backup automático do `postgres_data`
- [ ] Configurar variáveis de e-mail para envio real
- [ ] Expor logs do scheduler (`/var/log/cron.log`)
- [ ] Testar healthcheck dos containers

---

Próximo: [[modulos]]
