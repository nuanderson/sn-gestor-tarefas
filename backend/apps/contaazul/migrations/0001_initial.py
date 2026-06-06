from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('companies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContaAzulToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token',  models.TextField(verbose_name='Access Token')),
                ('refresh_token', models.TextField(verbose_name='Refresh Token')),
                ('expires_at',    models.DateTimeField(verbose_name='Expira em')),
                ('criado_em',     models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('atualizado_em', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('empresa', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='contaazul_token',
                    to='companies.empresa',
                    verbose_name='Empresa',
                )),
            ],
            options={
                'verbose_name':        'Token Conta Azul',
                'verbose_name_plural': 'Tokens Conta Azul',
            },
        ),
        migrations.CreateModel(
            name='ContaAzulVencimento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contaazul_id',    models.CharField(max_length=100, verbose_name='ID Conta Azul')),
                ('tipo', models.CharField(
                    choices=[('pagar', 'A Pagar'), ('receber', 'A Receber')],
                    max_length=10,
                    verbose_name='Tipo',
                )),
                ('descricao',       models.CharField(max_length=500, verbose_name='Descrição')),
                ('valor',           models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Valor (R$)')),
                ('data_vencimento', models.DateField(verbose_name='Data de Vencimento')),
                ('data_pagamento',  models.DateField(blank=True, null=True, verbose_name='Data de Pagamento')),
                ('status', models.CharField(
                    choices=[
                        ('pendente',  'Pendente'),
                        ('pago',      'Pago'),
                        ('atrasado',  'Atrasado'),
                        ('cancelado', 'Cancelado'),
                    ],
                    default='pendente',
                    max_length=20,
                    verbose_name='Status',
                )),
                ('pessoa_nome',    models.CharField(blank=True, max_length=300, verbose_name='Pessoa / Empresa')),
                ('parcela_numero', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Parcela Nº')),
                ('parcela_total',  models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Total de Parcelas')),
                ('sincronizado_em', models.DateTimeField(auto_now=True, verbose_name='Sincronizado em')),
                ('empresa', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='vencimentos_contaazul',
                    to='companies.empresa',
                    verbose_name='Empresa',
                )),
            ],
            options={
                'verbose_name':        'Vencimento Conta Azul',
                'verbose_name_plural': 'Vencimentos Conta Azul',
                'ordering':            ['data_vencimento'],
            },
        ),
        migrations.AddConstraint(
            model_name='contaazulvencimento',
            constraint=models.UniqueConstraint(
                fields=['empresa', 'contaazul_id', 'tipo'],
                name='unique_vencimento_por_empresa',
            ),
        ),
    ]
