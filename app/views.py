from django.shortcuts import render

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Max, Prefetch
from legis.models import Materia, Tramitacao


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Prefetch only the 2 most recent tramitacoes per materia
        ultimas_trams = Tramitacao.objects.order_by('-data')
        prefetch_trams = Prefetch(
            'tramitacoes',
            queryset=ultimas_trams,
            to_attr='ultimas_tramitacoes',
        )

        context['destaques'] = (
            Materia.objects
            .annotate(ultima_tram=Max('tramitacoes__data'))
            .filter(ultima_tram__isnull=False)
            .prefetch_related(prefetch_trams, 'autores__vereador')
            .order_by('-ultima_tram')[:20]
        )
        return context


class LoginView(TemplateView):
    template_name = 'login.html'

class PrivacyPolicyView(TemplateView):
    template_name = 'privacy_policy.html'

class TermsOfServiceView(TemplateView):
    template_name = 'terms_of_service.html'