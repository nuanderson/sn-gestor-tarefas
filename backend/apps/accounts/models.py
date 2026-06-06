"""
Modelo de usuário personalizado do SN Gestor.
Substitui o User padrão do Django para adicionar
perfis de acesso e campos específicos do sistema.
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UsuarioManager(BaseUserManager):
    """
    Manager customizado que usa email como identificador único
    no lugar do username padrão do Django.
    """
    def create_user(self, email, nome, password=None, **extra_fields):
        if not email:
            raise ValueError('O e-mail é obrigatório.')
        if not nome:
            raise ValueError('O nome é obrigatório.')
        email = self.normalize_email(email)
        user = self.model(email=email, nome=nome, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nome, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('perfil', 'admin')
        return self.create_user(email, nome, password, **extra_fields)


class Usuario(AbstractUser):
    """
    Usuário do SN Gestor.

    Perfis disponíveis:
    - admin      → acesso total ao sistema
    - manager    → gestor — cria tarefas, vê todos os dashboards
    - analyst    → analista — executa suas tarefas
    - assistant  → assistente — executa suas tarefas
    - client     → cliente — acessa apenas o portal do cliente
    """

    PERFIL_CHOICES = [
        ('admin',     'Administrador'),
        ('manager',   'Gestor'),
        ('analyst',   'Analista'),
        ('assistant', 'Assistente'),
        ('client',    'Cliente'),
    ]

    # Remove o campo username — usamos email como login
    username = None

    # Campos principais
    email    = models.EmailField('E-mail', unique=True)
    nome     = models.CharField('Nome completo', max_length=150)
    perfil   = models.CharField(
        'Perfil de acesso',
        max_length=20,
        choices=PERFIL_CHOICES,
        default='analyst',
    )
    cargo    = models.CharField('Cargo / Função', max_length=100, blank=True)
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    empresa_cliente = models.ForeignKey(
        'companies.Empresa',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='usuarios_clientes',
        verbose_name='Empresa (portal cliente)',
    )

    # Controle
    criado_em     = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    # Usa email como campo de login
    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['nome']

    objects = UsuarioManager()

    class Meta:
        verbose_name          = 'Usuário'
        verbose_name_plural   = 'Usuários'
        ordering              = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.get_perfil_display()})'

    # ── Propriedades de conveniência ────────────────
    @property
    def primeiro_nome(self):
        return self.nome.split()[0]

    @property
    def iniciais(self):
        partes = self.nome.strip().split()
        if len(partes) >= 2:
            return f'{partes[0][0]}{partes[-1][0]}'.upper()
        return partes[0][:2].upper() if partes else 'SN'

    @property
    def is_admin(self):
        return self.perfil == 'admin' or self.is_superuser

    @property
    def is_gestor_ou_acima(self):
        return self.perfil in ('admin', 'manager') or self.is_superuser

    @property
    def is_cliente(self):
        return self.perfil == 'client'
