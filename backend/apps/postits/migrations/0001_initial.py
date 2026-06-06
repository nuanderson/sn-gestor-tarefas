from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PostIt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('texto', models.TextField(verbose_name='Texto')),
                ('cor', models.CharField(
                    choices=[
                        ('amarelo', 'Amarelo'), ('verde', 'Verde'), ('azul', 'Azul'),
                        ('rosa', 'Rosa'), ('roxo', 'Roxo'),
                    ],
                    default='amarelo', max_length=10, verbose_name='Cor',
                )),
                ('visibilidade', models.CharField(
                    choices=[('privado', 'Privado — só eu vejo'), ('equipe', 'Equipe — todos veem')],
                    default='privado', max_length=10, verbose_name='Visibilidade',
                )),
                ('fixado', models.BooleanField(
                    default=False,
                    help_text='Post-its fixados aparecem sempre no topo',
                    verbose_name='Fixado',
                )),
                ('ordem', models.PositiveSmallIntegerField(
                    default=0,
                    help_text='Posição no quadro (menor = mais à esquerda/topo)',
                    verbose_name='Ordem',
                )),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('autor', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='postits',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Autor',
                )),
            ],
            options={
                'verbose_name': 'Post-it',
                'verbose_name_plural': 'Post-its',
                'ordering': ['-fixado', 'ordem', '-criado_em'],
            },
        ),
    ]
