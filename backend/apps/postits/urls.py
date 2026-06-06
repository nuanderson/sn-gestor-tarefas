from django.urls import path
from . import views

urlpatterns = [
    path('postits/',              views.PostItListCreateView.as_view(), name='postit-list'),
    path('postits/<int:pk>/',     views.PostItDetailView.as_view(),     name='postit-detail'),
    path('postits/<int:pk>/fixar/', views.PostItFixarView.as_view(),    name='postit-fixar'),
]
