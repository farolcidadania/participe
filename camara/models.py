from django.db import models

# Create your models here.

class Partido(models.Model):
    nome = models.CharField(max_length=255)
    sigla = models.CharField(max_length=50)

    def __str__(self):
        return self.sigla

class Vereador(models.Model):
    nome = models.CharField(max_length=255)
    imagem = models.URLField(null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    funcao = models.CharField(max_length=255, null=True, blank=True)

    camara_id = models.IntegerField(null=True, blank=True)
    

    partido = models.ForeignKey(Partido, on_delete=models.SET_NULL, null=True, blank=True)
    ativo = models.BooleanField(default=True)
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)
    data_desativacao = models.DateField(null=True, blank=True)
    

    def __str__(self):
        if self.partido:
            return f"{self.nome} ({self.partido.sigla})"
        return self.nome

class Comissao(models.Model):
    nome = models.CharField(max_length=255)
