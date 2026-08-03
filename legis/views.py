from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.db.models import Prefetch
from .models import Materia, Tramitacao, PROPOSICAO_TIPO


class ProjetosView(ListView):
    model = Materia
    template_name = 'legis/projetos.html'
    context_object_name = 'projetos'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related(
            'autores',
            Prefetch('tramitacoes', queryset=Tramitacao.objects.order_by('-data'))
        )

        tipo = self.request.GET.get('tipo')
        ano = self.request.GET.get('ano')
        q = self.request.GET.get('q')

        if tipo:
            qs = qs.filter(tipo=tipo)
        if ano:
            try:
                qs = qs.filter(ano=int(ano))
            except (ValueError, TypeError):
                pass
        if q:
            qs = qs.filter(ementa__icontains=q)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipos'] = PROPOSICAO_TIPO
        context['anos'] = (
            Materia.objects
            .exclude(ano__isnull=True)
            .values_list('ano', flat=True)
            .distinct()
            .order_by('-ano')
        )
        return context


class MateriaDetailView(DetailView):
    model = Materia
    template_name = 'legis/detalhe.html'
    context_object_name = 'materia'

    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            'autores__vereador',
            Prefetch('tramitacoes', queryset=Tramitacao.objects.order_by('-data'))
        )