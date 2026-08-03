from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from .views import HomeView, PrivacyPolicyView, TermsOfServiceView
from django.conf import settings
from django.conf.urls.static import static


from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('accounts/', include('allauth.urls')),
    
    #apps
    path("integrations/", include('ingest.urls')),
    path("projetos/", include('legis.urls')),
    path("", include('social.urls')),

    
    # Views customizadas
    path('', HomeView.as_view(), name='home'),
    path('termos-e-condicoes/', TermsOfServiceView.as_view(), name='terms_of_service'),
    path('privacidade/', PrivacyPolicyView.as_view(), name='privacy_policy'),
    path("login/", auth_views.LoginView.as_view(template_name="account/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
