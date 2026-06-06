from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MetaMensal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mes', models.PositiveSmallIntegerField(
                    help_text='1 = Janeiro, 12 = Dezembro',
                    validators=[django.core.validators.MinValueValidator(1)],
                    verbose_name='Mês',
                )),
                ('ano', models.PositiveSmallIntegerField(verbose_name='Ano')),
                ('meta_tarefas', models.PositiveSmallIntegerField(
                    default=0,
                    help_text='Quantas tarefas o colaborador deve concluir neste mês',
                    verbose_name='Meta de tarefas concluídas',
                )),
                ('meta_horas', models.PositiveSmallIntegerField(
                    default=0,
                    help_text='Quantas horas de timer o colaborador deve registrar',
                    verbose_name='Meta de horas registradas',
                )),
                ('observacao', models.TextField(blank=True, verbose_name='Observação')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('colaborador', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='metas_mensais',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Colaborador',
                )),
                ('criado_por', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='metas_criadas',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Criado por',
                )),
            ],
            options={
                'verbose_name': 'Meta Mensal',
                'verbose_name_plural': 'Metas Mensais',
                'ordering': ['-ano', '-mes', 'colaborador__nome'],
                'unique_together': {('colaborador', 'mes', 'ano')},
            },
        ),
    ]
