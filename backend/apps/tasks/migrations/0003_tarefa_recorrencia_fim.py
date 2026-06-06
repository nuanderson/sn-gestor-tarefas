from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_alter_checklistitem_options_alter_comentario_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tarefa',
            name='recorrencia_fim',
            field=models.DateField(
                blank=True,
                help_text='Se informado, todas as ocorrências são criadas de uma vez até esta data.',
                null=True,
                verbose_name='Repetir até',
            ),
        ),
    ]
