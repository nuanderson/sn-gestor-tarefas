from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contaazul', '0001_initial'),
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contaazulvencimento',
            name='tarefa',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='vencimento_contaazul',
                to='tasks.tarefa',
                verbose_name='Tarefa gerada',
            ),
        ),
    ]
