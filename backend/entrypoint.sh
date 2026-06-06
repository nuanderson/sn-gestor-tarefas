#!/bin/sh

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SN Gestor — Iniciando backend..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Aguarda o banco de dados ficar pronto
echo "⏳ Aguardando banco de dados..."
while ! nc -z db 5432; do
  sleep 1
done
echo "✅ Banco de dados pronto!"

# Aplica as migrations
echo "🔄 Aplicando migrations..."
python manage.py migrate --noinput

# Coleta arquivos estáticos
echo "📦 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear 2>/dev/null || true

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Escolhe o servidor conforme o modo (DEBUG=True → dev server, caso contrário → Gunicorn)
if [ "$DEBUG" = "True" ] || [ "$DEBUG" = "true" ] || [ "$DEBUG" = "1" ]; then
  echo "🔧 Modo desenvolvimento — Django runserver"
  python manage.py runserver 0.0.0.0:8000
else
  echo "🚀 Modo produção — Gunicorn (3 workers)"
  exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --worker-class sync \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
fi
