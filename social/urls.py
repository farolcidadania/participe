from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    path('perfil/', views.MyProfile.as_view(), name='my_profile'),
    path('perfil/configuracoes/', views.AccountSettings.as_view(), name='account_settings'),
]
