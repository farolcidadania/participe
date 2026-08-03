from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.views.generic import TemplateView, View

from .models import Perfil
from .forms import AvatarForm, BioForm, AccountForm


class MyProfile(LoginRequiredMixin, TemplateView):
    template_name = 'social/my_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        perfil, _ = Perfil.objects.get_or_create(user=user)

        context['user'] = user
        context['perfil'] = perfil
        # Allauth: e-mails vinculados e contas sociais
        context['email_addresses'] = user.emailaddress_set.all().order_by('-primary', '-verified')
        context['social_accounts'] = user.socialaccount_set.all()
        return context


class AccountSettings(LoginRequiredMixin, View):
    template_name = 'social/account_settings.html'

    def get_perfil(self):
        perfil, _ = Perfil.objects.get_or_create(user=self.request.user)
        return perfil

    def get(self, request, *args, **kwargs):
        from django.shortcuts import render
        perfil = self.get_perfil()
        context = {
            'user': request.user,
            'perfil': perfil,
            'avatar_form': AvatarForm(instance=perfil),
            'bio_form': BioForm(instance=perfil),
            'account_form': AccountForm(instance=request.user),
            # Allauth
            'email_addresses': request.user.emailaddress_set.all().order_by('-primary'),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        from django.shortcuts import render
        perfil = self.get_perfil()
        action = request.POST.get('action', '')

        if action == 'avatar':
            form = AvatarForm(request.POST, request.FILES, instance=perfil)
            if form.is_valid():
                form.save()
                messages.success(request, 'Foto de perfil atualizada com sucesso!')
                return redirect('social:account_settings')
            context = {
                'user': request.user,
                'perfil': perfil,
                'avatar_form': form,
                'bio_form': BioForm(instance=perfil),
                'email_addresses': request.user.emailaddress_set.all().order_by('-primary'),
            }
            return render(request, self.template_name, context)

        elif action == 'bio':
            form = BioForm(request.POST, instance=perfil)
            if form.is_valid():
                form.save()
                messages.success(request, 'Biografia atualizada!')
                return redirect('social:account_settings')
            context = {
                'user': request.user,
                'perfil': perfil,
                'avatar_form': AvatarForm(instance=perfil),
                'bio_form': form,
                'email_addresses': request.user.emailaddress_set.all().order_by('-primary'),
            }
            return render(request, self.template_name, context)

        elif action == 'account':
            form = AccountForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Conta atualizada!')
                return redirect('social:account_settings')
            context = {
                'user': request.user,
                'perfil': perfil,
                'avatar_form': AvatarForm(instance=perfil),
                'bio_form': BioForm(instance=perfil),
                'account_form': form,
                'email_addresses': request.user.emailaddress_set.all().order_by('-primary'),
            }
            
        messages.error(request, 'Ação inválida.')
        return redirect('social:account_settings')