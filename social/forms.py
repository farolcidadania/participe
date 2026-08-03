from django import forms
from .models import Perfil
from django.contrib.auth.models import User
from django.utils import timezone

from django.conf import settings



class AvatarForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['avatar']
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={
                'accept': 'image/*',
                'class': 'file-input',
                'id': 'id_avatar',
            })
        }


class BioForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['bio', 'telefone', 'cep', 'cidade', 'estado', 'pais', 'rua', 'numero', 'complemento', 'date_birth', 'genero', 'termos_v1', 'receber_emails', 'public_email']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'textarea', 'rows': 3, 'placeholder': 'Escreva algo sobre você...'}),
            'telefone': forms.TextInput(attrs={'class': 'input mask-phone', 'placeholder': '(00) 00000-0000'}),
            'cep': forms.TextInput(attrs={'class': 'input mask-cep', 'placeholder': '00000-000', 'required': True}),
            'cidade': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Cidade'}),
            'estado': forms.TextInput(attrs={'class': 'input', 'placeholder': 'UF'}),
            'pais': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Brasil'}),
            'rua': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Rua/Avenida'}),
            'numero': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Nº'}),
            'complemento': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Apto, Bloco, etc.'}),
            'date_birth': forms.DateInput(attrs={'class': 'input', 'type': 'date', 'required': True}, format='%Y-%m-%d'),
            'genero': forms.Select(attrs={'class': 'select'}),
        }

    def clean_date_birth(self):
        date_birth = self.cleaned_data.get('date_birth')
        if not date_birth:
            return date_birth

        today = timezone.localdate()
        if date_birth > today:
            raise forms.ValidationError('A data de nascimento não pode ser maior que a data atual.')

        # Cálculo mais preciso de idade (aproximado por dias)
        min_age_days = settings.DATE_OF_BIRTH_MIN * 365.25
        if (today - date_birth).days < min_age_days:
            raise forms.ValidationError(f'Você deve ter pelo menos {settings.DATE_OF_BIRTH_MIN} anos para se cadastrar.')
        
        return date_birth


class AccountForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Usuário',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Nome',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Sobrenome',
            }),
        }