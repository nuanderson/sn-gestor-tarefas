"""
Comando: python manage.py enviar_relatorio_semanal

Roda toda segunda-feira (08h via cron).
Envia para admins e gestores um resumo da semana anterior
e as tarefas que vencem na semana atual.
"""
from datetime import date, timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.db.models import Count, Sum, Q
from django.conf import settings

from apps.tasks.models import Tarefa, SessaoTarefa
from apps.accounts.models import Usuario


class Command(BaseCommand):
    help = 'Envia relatório semanal para gestores toda segunda-feira'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força o envio mesmo que não seja segunda-feira',
        )

    def handle(self, *args, **options):
        hoje = date.today()

        # Só roda em segunda-feira (weekday 0), a não ser que --force
        if hoje.weekday() != 0 and not options['force']:
            self.stdout.write('Hoje não é segunda-feira. Use --force para forçar o envio.')
            return

        # Semana anterior: seg a dom
        inicio_semana_passada = hoje - timedelta(days=hoje.weekday() + 7)
        fim_semana_passada    = inicio_semana_passada + timedelta(days=6)

        # Semana atual: hoje a domingo
        inicio_semana_atual = hoje
        fim_semana_atual    = hoje + timedelta(days=6 - hoje.weekday())

        # ── Dados da semana passada ──────────────────────────────────
        concluidas = Tarefa.objects.filter(
            status='done',
            concluida_em__date__gte=inicio_semana_passada,
            concluida_em__date__lte=fim_semana_passada,
        )

        atrasadas_abertas = Tarefa.objects.filter(
            status__in=['pending', 'progress'],
            prazo__lt=hoje,
        )

        minutos_semana = SessaoTarefa.objects.filter(
            status='finalizada',
            iniciado_em__date__gte=inicio_semana_passada,
            iniciado_em__date__lte=fim_semana_passada,
        ).aggregate(total=Sum('duracao_minutos'))['total'] or 0

        horas_semana = round(minutos_semana / 60, 1)

        # Produtividade por colaborador na semana passada
        por_colaborador = (
            SessaoTarefa.objects.filter(
                status='finalizada',
                iniciado_em__date__gte=inicio_semana_passada,
                iniciado_em__date__lte=fim_semana_passada,
            )
            .values('usuario__nome')
            .annotate(horas=Sum('duracao_minutos'))
            .order_by('-horas')
        )
        por_colaborador_fmt = [
            {'nome': item['usuario__nome'], 'horas': round((item['horas'] or 0) / 60, 1)}
            for item in por_colaborador
        ]

        # ── Tarefas que vencem esta semana ───────────────────────────
        vencendo_semana = Tarefa.objects.filter(
            prazo__gte=inicio_semana_atual,
            prazo__lte=fim_semana_atual,
            status__in=['pending', 'progress'],
        ).select_related('empresa', 'responsavel').order_by('prazo')

        # ── Destinatários: admins e gestores ────────────────────────
        destinatarios = Usuario.objects.filter(
            perfil__in=['admin', 'manager'],
            is_active=True,
            email__isnull=False,
        ).exclude(email='')

        if not destinatarios.exists():
            self.stdout.write(self.style.WARNING('Nenhum gestor/admin com e-mail cadastrado.'))
            return

        context = {
            'inicio_semana_passada': inicio_semana_passada,
            'fim_semana_passada': fim_semana_passada,
            'inicio_semana_atual': inicio_semana_atual,
            'fim_semana_atual': fim_semana_atual,
            'concluidas': concluidas,
            'total_concluidas': concluidas.count(),
            'total_atrasadas': atrasadas_abertas.count(),
            'horas_semana': horas_semana,
            'por_colaborador': por_colaborador_fmt,
            'vencendo_semana': vencendo_semana,
            'total_vencendo': vencendo_semana.count(),
        }

        html_msg = render_to_string('relatorios/email_relatorio_semanal.html', context)
        texto_msg = (
            f'Relatório Semanal SN Gestor\n'
            f'Semana: {inicio_semana_passada.strftime("%d/%m")} a {fim_semana_passada.strftime("%d/%m/%Y")}\n\n'
            f'Tarefas concluídas: {context["total_concluidas"]}\n'
            f'Tarefas atrasadas em aberto: {context["total_atrasadas"]}\n'
            f'Horas registradas: {horas_semana}h\n\n'
            f'Tarefas vencendo esta semana: {context["total_vencendo"]}\n\n'
            f'SN Gestor'
        )

        enviados = 0
        for gestor in destinatarios:
            try:
                send_mail(
                    subject=f'[SN Gestor] Relatório Semanal — {inicio_semana_passada.strftime("%d/%m")} a {fim_semana_passada.strftime("%d/%m/%Y")}',
                    message=texto_msg,
                    html_message=html_msg,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[gestor.email],
                    fail_silently=False,
                )
                enviados += 1
            except Exception as exc:
                self.stderr.write(f'Erro ao enviar para {gestor.email}: {exc}')

        self.stdout.write(
            self.style.SUCCESS(f'Relatório semanal enviado para {enviados} destinatário(s).')
        )
