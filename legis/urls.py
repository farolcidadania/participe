from django.urls import path
from .views import ProjetosView, MateriaDetailView


app_name = 'legis'

urlpatterns = [
    path('', ProjetosView.as_view(), name='projetos'),
    path('projetos/<int:pk>/', MateriaDetailView.as_view(), name='detalhe'),
]