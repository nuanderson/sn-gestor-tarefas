"""
Views do Quadro de Post-its — Fase 7.

Regras:
  - Qualquer colaborador interno pode criar post-its
  - Listagem retorna: meus post-its (privados + equipe) + post-its de equipe de outros
  - Somente o autor pode editar, fixar/desafixar ou excluir o próprio post-it
  - Admins e gestores podem excluir qualquer post-it (moderação)

Endpoints:
  GET    /api/v1/postits/              → quadro completo (meus + equipe)
  POST   /api/v1/postits/              → criar post-it
  PUT    /api/v1/postits/<id>/         → editar (somente autor)
  PATCH  /api/v1/postits/<id>/fixar/   → fixar / desafixar (somente autor)
  DELETE /api/v1/postits/<id>/         → excluir (autor ou gestor/admin)
"""
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsEquipeInterna, IsGestorOuAcima
from .models import PostIt
from .serializers import PostItSerializer


class PostItListCreateView(APIView):
    """
    GET  → quadro completo do usuário logado
    POST → criar novo post-it
    """
    permission_classes = [IsEquipeInterna]

    def get(self, request):
        # Retorna:
        #   1. Todos os meus post-its (privados e de equipe)
        #   2. Post-its de EQUIPE de outros usuários
        qs = PostIt.objects.select_related('autor').filter(
            Q(autor=request.user) |
            Q(visibilidade='equipe')
        ).distinct()

        # Filtro opcional por visibilidade: ?visibilidade=privado ou equipe
        vis = request.query_params.get('visibilidade')
        if vis in ('privado', 'equipe'):
            qs = qs.filter(visibilidade=vis)

        serializer = PostItSerializer(qs, many=True, context={'request': request})

        # Separa em duas seções para facilitar o frontend
        dados = serializer.data
        meus    = [p for p in dados if p['e_meu']]
        equipe  = [p for p in dados if not p['e_meu'] and p['visibilidade'] == 'equipe']

        return Response({
            'meus': meus,
            'equipe': equipe,
            'total': len(dados),
        })

    def post(self, request):
        serializer = PostItSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(autor=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostItDetailView(APIView):
    """
    PUT    → editar texto/cor/visibilidade (somente autor)
    DELETE → excluir (autor ou gestor/admin)
    """
    permission_classes = [IsEquipeInterna]

    def _get_postit(self, pk):
        try:
            return PostIt.objects.select_related('autor').get(pk=pk)
        except PostIt.DoesNotExist:
            return None

    def _pode_editar(self, postit, usuario):
        return postit.autor_id == usuario.id

    def _pode_excluir(self, postit, usuario):
        return postit.autor_id == usuario.id or usuario.is_gestor_ou_acima

    def put(self, request, pk):
        postit = self._get_postit(pk)
        if not postit:
            return Response({'erro': 'Post-it não encontrado.'}, status=404)
        if not self._pode_editar(postit, request.user):
            return Response({'erro': 'Você só pode editar os seus próprios post-its.'}, status=403)

        serializer = PostItSerializer(postit, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        postit = self._get_postit(pk)
        if not postit:
            return Response({'erro': 'Post-it não encontrado.'}, status=404)
        if not self._pode_excluir(postit, request.user):
            return Response({'erro': 'Você não tem permissão para excluir este post-it.'}, status=403)
        postit.delete()
        return Response({'mensagem': 'Post-it removido.'}, status=204)


class PostItFixarView(APIView):
    """
    PATCH /api/v1/postits/<id>/fixar/
    Alterna fixado/não-fixado. Somente o autor.
    """
    permission_classes = [IsEquipeInterna]

    def patch(self, request, pk):
        try:
            postit = PostIt.objects.get(pk=pk)
        except PostIt.DoesNotExist:
            return Response({'erro': 'Post-it não encontrado.'}, status=404)

        if postit.autor_id != request.user.id:
            return Response({'erro': 'Você só pode fixar os seus próprios post-its.'}, status=403)

        postit.fixado = not postit.fixado
        postit.save(update_fields=['fixado'])

        acao = 'fixado' if postit.fixado else 'desfixado'
        return Response({
            'mensagem': f'Post-it {acao} com sucesso.',
            'fixado': postit.fixado,
        })
