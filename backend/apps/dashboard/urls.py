from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/geral/',          views.DashboardGeralView.as_view(),          name='dashboard-geral'),
    path('dashboard/individual/',     views.DashboardIndividualView.as_view(),     name='dashboard-individual'),
    path('dashboard/colaboradores/',  views.DashboardColaboradoresView.as_view(),  name='dashboard-colaboradores'),
    path('dashboard/metas/',          views.MetaMensalListCreateView.as_view(),    name='metas-list'),
    path('dashboard/metas/<int:pk>/', views.MetaMensalDetailView.as_view(),        name='metas-detail'),
]
