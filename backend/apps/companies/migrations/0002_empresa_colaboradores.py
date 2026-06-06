from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='empresa',
            name='colaboradores',
            field=models.ManyToManyField(
                blank=True,
                related_name='empresas_colaborador',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Colaboradores',
            ),
        ),
    ]
