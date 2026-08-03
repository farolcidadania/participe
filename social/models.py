from django.contrib.auth.models import User
from django.db import models


generos = [
    ('M', 'Masculino'),
    ('F', 'Feminino'),
    ('O', 'Outro'),
]

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, default='')
    
    telefone = models.CharField(max_length=11, blank=True, null=True)
    
    cep = models.CharField(max_length=8, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    rua = models.CharField(max_length=100, blank=True, null=True)
    numero = models.CharField(max_length=20, blank=True, null=True)
    complemento = models.CharField(max_length=100, blank=True, null=True)


    date_birth = models.DateField(blank=True, null=True, verbose_name='Aniversário')
    genero = models.CharField(max_length=1, blank=True, null=True, choices=generos)

    termos_v1 = models.BooleanField(default=False)
    receber_emails = models.BooleanField(default=True) 
    public_email = models.BooleanField(default=False)   

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'

    def __str__(self):
        return f'Perfil de {self.user.username}'

    def get_avatar_url(self):
        """Retorna o avatar uploaded, ou o avatar do provedor social (Google/Facebook)."""
        if self.avatar:
            return self.avatar.url
        social = self.user.socialaccount_set.first()
        if social:
            return social.get_avatar_url()
        return None
