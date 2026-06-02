"""
Comando: python manage.py enviar_alertas_prazo

Roda diariamente (08h via cron).
Para cada tarefa pendente/em-andamento com prazo = amanhã:
  1. Cria notificação interna para o responsável
  2. Envia e-mail para o responsável
Controle anti-duplicata: registra no campo `detalhe` do HistoricoTarefa.
"""
from datetime import date, timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.conf import settings

from apps.tasks.models import Tarefa, HistoricoTarefa
from apps.tasks.views_notificacoes import criar_notificacao


class Command(BaseCommand):
    help = 'Envia e-mails e notificações para tarefas que vencem amanhã'

    def handle(self, *args, **options):
        amanha = date.today() + timedelta(days=1)
        hoje_str = date.today().isoformat()

        tarefas = Tarefa.objects.filter(
            prazo=amanha,
            status__in=['pending', 'progress'],
            responsavel__isnull=False,
        ).select_related('responsavel', 'empresa')

        enviados = 0
        ignorados = 0

        for tarefa in tarefas:
            # Anti-duplicata: verifica se já enviou hoje
            ja_enviou = HistoricoTarefa.objects.filter(
                tarefa=tarefa,
                acao='timer',
                detalhe=f'alerta_prazo:{hoje_str}',
            ).exists()

            if ja_enviou:
                ignorados += 1
                continue

            responsavel = tarefa.responsavel

            # Notificação interna
            criar_notificacao(
                usuario=responsavel,
                tipo='tarefa_vencendo',
                titulo='Tarefa vence amanhã',
                mensagem=f'A tarefa "{tarefa.titulo}" da empresa {tarefa.empresa.nome} vence amanhã ({amanha.strftime("%d/%m/%Y")}).',
                tarefa=tarefa,
            )

            # E-mail
            if responsavel.email:
                context = {
                    'responsavel': responsavel,
                    'tarefa': tarefa,
                    'prazo': amanha,
                }
                html_msg = render_to_string('relatorios/email_alerta_prazo.html', context)
                texto_msg = (
                    f'Olá, {responsavel.primeiro_nome}!\n\n'
                    f'A tarefa "{tarefa.titulo}" da empresa {tarefa.empresa.nome} '
                    f'vence amanhã ({amanha.strftime("%d/%m/%Y")}).\n\n'
                    f'Acesse o SN Gestor para verificar.\n\nSN Gestor'
                )
                try:
                    send_mail(
                        subject=f'[SN Gestor] Tarefa vence amanhã: {tarefa.titulo}',
                        message=texto_msg,
                        html_message=html_msg,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[responsavel.email],
                        fail_silently=False,
                    )
                except Exception as exc:
                    self.stderr.write(f'Erro ao enviar e-mail para {responsavel.email}: {exc}')
                    continue

            # Marca como enviado (reusa HistoricoTarefa com acao=timer e detalhe especial)
            HistoricoTarefa.objects.create(
                tarefa=tarefa,
                usuario=None,
                acao='timer',
                detalhe=f'alerta_prazo:{hoje_str}',
            )
            enviados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Alertas de prazo: {enviados} enviado(s), {ignorados} ignorado(s) (já enviados hoje).'
            )
        )
