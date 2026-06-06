"""
Signals de Tarefas — Fase 6.
Cria notificações internas automaticamente quando eventos acontecem.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Tarefa, Comentario
from .views_notificacoes import criar_notificacao


@receiver(post_save, sender=Tarefa)
def notificar_tarefa(sender, instance, created, **kwargs):
    tarefa = instance

    if created:
        # Nova tarefa atribuída — avisa o responsável
        if tarefa.responsavel and tarefa.criado_por != tarefa.responsavel:
            criar_notificacao(
                usuario=tarefa.responsavel,
                tipo='tarefa_criada',
                titulo='Nova tarefa atribuída',
                mensagem=(
                    f'Você recebeu a tarefa "{tarefa.titulo}" '
                    f'da empresa {tarefa.empresa.nome}.'
                ),
                tarefa=tarefa,
            )
        return

    # Tarefa existente alterada — detecta mudança de status
    try:
        anterior = Tarefa.objects.get(pk=tarefa.pk)
    except Tarefa.DoesNotExist:
        return

    # Verifica se concluiu agora
    if tarefa.status == 'done' and tarefa.criado_por and tarefa.criado_por != tarefa.responsavel:
        criar_notificacao(
            usuario=tarefa.criado_por,
            tipo='tarefa_concluida',
            titulo='Tarefa concluída',
            mensagem=(
                f'A tarefa "{tarefa.titulo}" da empresa {tarefa.empresa.nome} '
                f'foi concluída por {tarefa.responsavel.nome if tarefa.responsavel else "alguém"}.'
            ),
            tarefa=tarefa,
        )


@receiver(post_save, sender=Comentario)
def notificar_comentario(sender, instance, created, **kwargs):
    if not created:
        return

    comentario = instance
    tarefa = comentario.tarefa
    autor = comentario.autor

    destinatarios = set()

    # Responsável recebe, exceto se foi ele mesmo que comentou
    if tarefa.responsavel and tarefa.responsavel != autor:
        destinatarios.add(tarefa.responsavel)

    # Criador da tarefa recebe, exceto se foi ele que comentou
    if tarefa.criado_por and tarefa.criado_por != autor:
        destinatarios.add(tarefa.criado_por)

    nome_autor = autor.nome if autor else 'Alguém'
    for usuario in destinatarios:
        criar_notificacao(
            usuario=usuario,
            tipo='comentario_novo',
            titulo='Novo comentário na tarefa',
            mensagem=(
                f'{nome_autor} comentou em "{tarefa.titulo}": '
                f'"{comentario.texto[:120]}{"..." if len(comentario.texto) > 120 else ""}"'
            ),
            tarefa=tarefa,
        )
