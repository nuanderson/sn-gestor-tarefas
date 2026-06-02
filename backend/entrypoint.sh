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

echo "🚀 Iniciando servidor Django..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Inicia o servidor de desenvolvimento
python manage.py runserver 0.0.0.0:8000
